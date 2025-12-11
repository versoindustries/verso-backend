import { useState, useCallback } from 'react'
import {
    DndContext,
    DragEndEvent,
    DragOverEvent,
    DragOverlay,
    DragStartEvent,
    closestCenter,
    PointerSensor,
    useSensor,
    useSensors,
    useDroppable,
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
        data: { lead, type: 'lead' }
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
            className={`kanban-card ${isDragging ? 'is-dragging' : ''}`}
        >
            <div className="kanban-card-header">
                <div {...attributes} {...listeners} className="drag-handle">
                    <GripVertical className="w-4 h-4" />
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

// Droppable Column Component - now with useDroppable for empty column drops
function KanbanColumn({
    stageName,
    column,
    leadDetailUrl,
    isOver,
}: {
    stageName: string
    column: Column
    leadDetailUrl: string
    isOver: boolean
}) {
    const { setNodeRef } = useDroppable({
        id: stageName,
        data: { type: 'column', stageName }
    })

    const leadIds = column.leads.map(l => `${l.type}-${l.id}`)

    return (
        <div className={`kanban-column ${isOver ? 'drop-target' : ''}`}>
            <div
                className="kanban-column-header"
                style={{ '--column-color': column.stage.color } as React.CSSProperties}
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
                <div
                    ref={setNodeRef}
                    className={`kanban-column-body ${isOver ? 'is-over' : ''}`}
                    data-status={stageName}
                >
                    {column.leads.map((lead) => (
                        <LeadCard
                            key={`${lead.type}-${lead.id}`}
                            lead={lead}
                            leadDetailUrl={leadDetailUrl}
                        />
                    ))}
                    {column.leads.length === 0 && (
                        <div className={`empty-column ${isOver ? 'active' : ''}`}>
                            <span className="empty-icon">📥</span>
                            <span>Drop leads here</span>
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
    const [overColumn, setOverColumn] = useState<string | null>(null)
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

    const handleDragOver = useCallback((event: DragOverEvent) => {
        const { over } = event
        if (!over) {
            setOverColumn(null)
            return
        }

        // Check if hovering over a column directly
        if (over.data.current?.type === 'column') {
            setOverColumn(over.data.current.stageName)
            return
        }

        // Check if hovering over a lead in a column
        if (over.data.current?.sortable) {
            // Find which column contains this lead
            const overId = over.id as string
            for (const [stageName, col] of Object.entries(columns)) {
                const leadIds = col.leads.map(l => `${l.type}-${l.id}`)
                if (leadIds.includes(overId)) {
                    setOverColumn(stageName)
                    return
                }
            }
        }

        // Check if over.id is a stage name (column)
        if (typeof over.id === 'string' && columns[over.id]) {
            setOverColumn(over.id)
            return
        }

        setOverColumn(null)
    }, [columns])

    const handleDragEnd = useCallback(async (event: DragEndEvent) => {
        const { active, over } = event
        setActiveId(null)
        setActiveLead(null)
        setOverColumn(null)

        if (!over) return

        // Determine target column
        let targetStatus: string | null = null

        // Priority 1: Dropped on a column directly (from useDroppable)
        if (over.data.current?.type === 'column') {
            targetStatus = over.data.current.stageName
        }

        // Priority 2: Dropped on a lead card - get its column
        if (!targetStatus && over.data.current?.lead) {
            const overId = over.id as string
            for (const [stageName, col] of Object.entries(columns)) {
                const leadIds = col.leads.map(l => `${l.type}-${l.id}`)
                if (leadIds.includes(overId)) {
                    targetStatus = stageName
                    break
                }
            }
        }

        // Priority 3: over.id is a stage name directly
        if (!targetStatus && typeof over.id === 'string' && columns[over.id]) {
            targetStatus = over.id
        }

        if (!targetStatus) return

        // Extract lead info from activeId
        const activeIdStr = active.id as string
        const dashIndex = activeIdStr.indexOf('-')
        const type = activeIdStr.substring(0, dashIndex)
        const id = parseInt(activeIdStr.substring(dashIndex + 1), 10)

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

    const handleDragCancel = useCallback(() => {
        setActiveId(null)
        setActiveLead(null)
        setOverColumn(null)
    }, [])

    return (
        <div className="kanban-board">
            <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDragEnd={handleDragEnd}
                onDragCancel={handleDragCancel}
            >
                <div className="kanban-columns">
                    {Object.entries(columns).map(([stageName, column]) => (
                        <KanbanColumn
                            key={stageName}
                            stageName={stageName}
                            column={column}
                            leadDetailUrl={leadDetailUrl}
                            isOver={overColumn === stageName}
                        />
                    ))}
                </div>

                <DragOverlay dropAnimation={null}>
                    {activeId && activeLead ? (
                        <div className="kanban-card drag-overlay">
                            <div className="kanban-card-header">
                                <div className="drag-handle">
                                    <GripVertical className="w-4 h-4" />
                                </div>
                                <span className="lead-name">{activeLead.name}</span>
                                {activeLead.score > 0 && (
                                    <span className="lead-score">{activeLead.score}</span>
                                )}
                            </div>
                            <div className="kanban-card-body">
                                <p className="lead-contact">
                                    <Mail className="w-3 h-3" /> {activeLead.email}
                                </p>
                            </div>
                        </div>
                    ) : null}
                </DragOverlay>
            </DndContext>
        </div>
    )
}
