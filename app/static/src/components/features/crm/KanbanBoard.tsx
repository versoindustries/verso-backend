import { useState, useCallback } from 'react'
import {
    DndContext,
    DragEndEvent,
    DragOverlay,
    DragStartEvent,
    closestCorners,
    PointerSensor,
    useSensor,
    useSensors,
} from '@dnd-kit/core'
import {
    SortableContext,
    verticalListSortingStrategy,
    useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Mail, Phone, Link2, GripVertical } from 'lucide-react'
import { useToastApi } from '../../../hooks/useToastApi'

interface Lead {
    id: number
    type: 'contact' | 'appointment'
    name: string
    email: string
    phone: string
    date: string
    source: string
    score: number
}

interface Stage {
    name: string
    color: string
}

interface Column {
    stage: Stage
    leads: Lead[]
}

interface KanbanBoardProps {
    columns: Record<string, Column>
    updateStatusUrl: string
    leadDetailUrl: string
}

// Sortable Lead Card Component
function LeadCard({ lead, leadDetailUrl }: { lead: Lead; leadDetailUrl: string }) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({
        id: `${lead.type}-${lead.id}`,
        data: { lead }
    })

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    }

    const detailUrl = leadDetailUrl
        .replace('__TYPE__', lead.type)
        .replace('__ID__', String(lead.id))

    return (
        <div
            ref={setNodeRef}
            style={style}
            className="kanban-card"
        >
            <div className="kanban-card-header">
                <div {...attributes} {...listeners} className="drag-handle">
                    <GripVertical className="w-4 h-4 text-gray-400" />
                </div>
                <a href={detailUrl} className="lead-name">
                    {lead.name}
                </a>
                {lead.score > 0 && (
                    <span className="lead-score">{lead.score}</span>
                )}
            </div>

            <div className="kanban-card-body">
                <p className="lead-contact">
                    <Mail className="w-3 h-3" /> {lead.email}
                </p>
                <p className="lead-contact">
                    <Phone className="w-3 h-3" /> {lead.phone}
                </p>

                <div className="lead-meta">
                    <span className={`lead-type-badge ${lead.type}`}>
                        {lead.type === 'appointment' ? 'Appointment' : 'Contact'}
                    </span>
                    <span className="lead-date">
                        {lead.date ? new Date(lead.date).toLocaleDateString() : 'N/A'}
                    </span>
                </div>

                {lead.source && lead.source !== 'unknown' && (
                    <p className="lead-source">
                        <Link2 className="w-3 h-3" /> {lead.source}
                    </p>
                )}
            </div>
        </div>
    )
}

// Droppable Column Component
function KanbanColumn({
    stageName,
    column,
    leadDetailUrl,
}: {
    stageName: string
    column: Column
    leadDetailUrl: string
}) {
    const leadIds = column.leads.map(l => `${l.type}-${l.id}`)

    return (
        <div className="kanban-column">
            <div
                className="kanban-column-header"
                style={{ borderTopColor: column.stage.color }}
            >
                <span className="stage-name">{stageName}</span>
                <span
                    className="lead-count"
                    style={{ backgroundColor: column.stage.color }}
                >
                    {column.leads.length}
                </span>
            </div>

            <SortableContext items={leadIds} strategy={verticalListSortingStrategy}>
                <div className="kanban-column-body" data-status={stageName}>
                    {column.leads.map((lead) => (
                        <LeadCard
                            key={`${lead.type}-${lead.id}`}
                            lead={lead}
                            leadDetailUrl={leadDetailUrl}
                        />
                    ))}
                    {column.leads.length === 0 && (
                        <div className="empty-column">
                            Drop leads here
                        </div>
                    )}
                </div>
            </SortableContext>
        </div>
    )
}

export default function KanbanBoard({
    columns: initialColumns,
    updateStatusUrl,
    leadDetailUrl,
}: KanbanBoardProps) {
    const [columns, setColumns] = useState(initialColumns)
    const [activeId, setActiveId] = useState<string | null>(null)
    const [activeLead, setActiveLead] = useState<Lead | null>(null)
    const api = useToastApi()

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        })
    )

    const handleDragStart = useCallback((event: DragStartEvent) => {
        const { active } = event
        setActiveId(active.id as string)
        setActiveLead(active.data.current?.lead || null)
    }, [])

    const handleDragEnd = useCallback(async (event: DragEndEvent) => {
        const { active, over } = event
        setActiveId(null)
        setActiveLead(null)

        if (!over) return

        // Find which column the item was dropped into
        const overId = over.id as string
        let targetStatus: string | null = null

        // Check if dropped on a column
        for (const [stageName, col] of Object.entries(columns)) {
            const leadIds = col.leads.map(l => `${l.type}-${l.id}`)
            if (leadIds.includes(overId) || over.data.current?.sortable?.containerId === stageName) {
                targetStatus = stageName
                break
            }
        }

        // If dropped directly on a column body
        if (!targetStatus && typeof over.id === 'string') {
            // Check if overId matches a stage name
            if (columns[over.id]) {
                targetStatus = over.id
            }
        }

        if (!targetStatus) {
            // Try to find from the droppable element's data-status
            const el = document.querySelector(`[data-status="${overId}"]`)
            if (el) {
                targetStatus = el.getAttribute('data-status')
            }
        }

        if (!targetStatus) return

        // Extract lead info from activeId
        const [type, idStr] = (active.id as string).split('-')
        const id = parseInt(idStr, 10)

        // Find current column and lead
        let currentColumn: string | null = null
        let lead: Lead | null = null

        for (const [stageName, col] of Object.entries(columns)) {
            const found = col.leads.find(l => l.type === type && l.id === id)
            if (found) {
                currentColumn = stageName
                lead = found
                break
            }
        }

        if (!lead || currentColumn === targetStatus) return

        // Optimistically update UI
        const newColumns = { ...columns }
        if (currentColumn) {
            newColumns[currentColumn] = {
                ...newColumns[currentColumn],
                leads: newColumns[currentColumn].leads.filter(l => !(l.type === type && l.id === id))
            }
        }
        newColumns[targetStatus] = {
            ...newColumns[targetStatus],
            leads: [...newColumns[targetStatus].leads, lead]
        }
        setColumns(newColumns)

        // Send update to server
        const response = await api.post<{ success: boolean; error?: string }>(
            updateStatusUrl,
            { id, type, status: targetStatus },
            { errorMessage: 'Failed to update lead status' }
        )

        if (!response.ok || !response.data?.success) {
            // Revert on failure
            setColumns(initialColumns)
        }
    }, [columns, initialColumns, updateStatusUrl, api])

    return (
        <div className="kanban-board">
            <DndContext
                sensors={sensors}
                collisionDetection={closestCorners}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
            >
                <div className="kanban-columns">
                    {Object.entries(columns).map(([stageName, column]) => (
                        <KanbanColumn
                            key={stageName}
                            stageName={stageName}
                            column={column}
                            leadDetailUrl={leadDetailUrl}
                        />
                    ))}
                </div>

                <DragOverlay>
                    {activeId && activeLead ? (
                        <div className="kanban-card dragging">
                            <div className="kanban-card-header">
                                <span className="lead-name">{activeLead.name}</span>
                            </div>
                        </div>
                    ) : null}
                </DragOverlay>
            </DndContext>
        </div>
    )
}
