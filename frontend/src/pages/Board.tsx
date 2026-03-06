import { useEffect, useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from "@dnd-kit/core";
import { useDroppable } from "@dnd-kit/core";
import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { api, type Post, type Favorite } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { GripVertical, Trash2, ExternalLink } from "lucide-react";

type KanbanItem = Post & Favorite;

const COLUMNS = [
  { id: "new", label: "New" },
  { id: "researching", label: "Researching" },
  { id: "has_potential", label: "Has Potential" },
  { id: "parked", label: "Parked" },
] as const;

const CATEGORY_COLORS: Record<string, string> = {
  missing_product: "bg-orange-100 text-orange-800",
  tooling_gap: "bg-violet-100 text-violet-800",
  workflow_friction: "bg-cyan-100 text-cyan-800",
  integration_gap: "bg-pink-100 text-pink-800",
  price_complaint: "bg-yellow-100 text-yellow-800",
  other: "bg-gray-100 text-gray-800",
};

const SEVERITY_DOT: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-yellow-500",
  low: "bg-green-500",
};

function DroppableColumn({
  id,
  label,
  items,
  onCardClick,
  onRemove,
}: {
  id: string;
  label: string;
  items: KanbanItem[];
  onCardClick: (item: KanbanItem) => void;
  onRemove: (item: KanbanItem) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={`flex-1 min-w-[260px] rounded-xl p-3 transition-colors ${
        isOver ? "bg-accent/80 ring-2 ring-primary/20" : "bg-muted/50"
      }`}
    >
      <div className="flex items-center gap-2 mb-3 px-1">
        <h3 className="font-semibold text-sm">{label}</h3>
        <Badge variant="secondary" className="text-xs">
          {items.length}
        </Badge>
      </div>
      <div className="space-y-2 min-h-[100px]">
        {items.map((item) => (
          <DraggableCard
            key={item.post_id}
            item={item}
            onCardClick={onCardClick}
            onRemove={onRemove}
          />
        ))}
      </div>
    </div>
  );
}

function DraggableCard({
  item,
  onCardClick,
  onRemove,
}: {
  item: KanbanItem;
  onCardClick: (item: KanbanItem) => void;
  onRemove: (item: KanbanItem) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: item.post_id });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div ref={setNodeRef} style={style}>
      <Card
        className="shadow-sm hover:shadow-md transition-shadow cursor-pointer"
        onClick={() => onCardClick(item)}
      >
        <CardContent className="p-3 space-y-2">
          <div className="flex items-start gap-1">
            <button
              {...listeners}
              {...attributes}
              className="mt-0.5 text-muted-foreground hover:text-foreground cursor-grab active:cursor-grabbing"
              onClick={(e) => e.stopPropagation()}
            >
              <GripVertical className="w-4 h-4" />
            </button>
            <p className="text-sm font-medium leading-snug flex-1">
              {item.summary ?? item.title}
            </p>
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            <Badge variant="secondary" className="text-xs font-normal">
              r/{item.subreddit}
            </Badge>
            {item.category && (
              <Badge
                className={`text-xs font-normal border-none ${CATEGORY_COLORS[item.category] ?? CATEGORY_COLORS.other}`}
              >
                {item.category.replace(/_/g, " ")}
              </Badge>
            )}
            {item.severity && (
              <span className="flex items-center gap-1">
                <span
                  className={`w-2 h-2 rounded-full ${SEVERITY_DOT[item.severity] ?? ""}`}
                />
                <span className="text-xs text-muted-foreground capitalize">
                  {item.severity}
                </span>
              </span>
            )}
          </div>
          {item.notes && (
            <p className="text-xs text-muted-foreground bg-muted rounded p-1.5 line-clamp-2">
              {item.notes}
            </p>
          )}
          <div className="flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(item);
              }}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function CardOverlay({ item }: { item: KanbanItem }) {
  return (
    <Card className="shadow-lg w-[260px] rotate-2">
      <CardContent className="p-3">
        <p className="text-sm font-medium leading-snug">
          {item.summary ?? item.title}
        </p>
        <Badge variant="secondary" className="text-xs font-normal mt-1">
          r/{item.subreddit}
        </Badge>
      </CardContent>
    </Card>
  );
}

function DetailDialog({
  item,
  open,
  onClose,
  onSaveNotes,
}: {
  item: KanbanItem | null;
  open: boolean;
  onClose: () => void;
  onSaveNotes: (item: KanbanItem, notes: string) => void;
}) {
  const [notesText, setNotesText] = useState("");

  useEffect(() => {
    if (item) setNotesText(item.notes || "");
  }, [item]);

  if (!item) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-base leading-snug pr-6">
            {item.summary ?? item.title}
          </DialogTitle>
        </DialogHeader>

        {/* Meta badges */}
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Badge variant="secondary" className="font-normal">
            r/{item.subreddit}
          </Badge>
          {item.category && (
            <Badge
              className={`font-normal border-none ${CATEGORY_COLORS[item.category] ?? CATEGORY_COLORS.other}`}
            >
              {item.category.replace(/_/g, " ")}
            </Badge>
          )}
          {item.severity && (
            <span className="flex items-center gap-1">
              <span
                className={`w-2 h-2 rounded-full ${SEVERITY_DOT[item.severity] ?? ""}`}
              />
              <span className="text-muted-foreground capitalize">{item.severity}</span>
            </span>
          )}
          {item.willingness_to_pay && item.willingness_to_pay !== "unlikely" && (
            <Badge
              variant="outline"
              className="font-normal text-green-700 border-green-300"
            >
              WTP: {item.willingness_to_pay}
            </Badge>
          )}
          {item.has_existing_solution && (
            <Badge
              variant="outline"
              className="font-normal text-amber-700 border-amber-300"
            >
              Has solution
            </Badge>
          )}
          <span className="text-muted-foreground ml-auto">
            {item.score} pts · {item.num_comments} comments
          </span>
        </div>

        <Separator />

        {/* Original post */}
        <div className="space-y-2 text-sm">
          <p className="font-medium">{item.title}</p>
          {item.selftext && (
            <p className="text-muted-foreground whitespace-pre-wrap">
              {item.selftext}
            </p>
          )}
        </div>

        {/* Existing solution notes */}
        {item.existing_solution_notes && (
          <div className="bg-amber-50 rounded-md p-3 text-sm text-amber-900">
            <span className="font-medium">Existing solutions: </span>
            {item.existing_solution_notes}
          </div>
        )}

        {/* Tags */}
        {item.relevance_tags && item.relevance_tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {item.relevance_tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs font-normal">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
        >
          View on Reddit <ExternalLink className="w-3 h-3" />
        </a>

        <Separator />

        {/* Notes */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Your Notes</p>
          <Textarea
            value={notesText}
            onChange={(e) => setNotesText(e.target.value)}
            placeholder="Add your research notes..."
            rows={4}
          />
          <div className="flex justify-end">
            <Button
              size="sm"
              onClick={() => {
                onSaveNotes(item, notesText);
                onClose();
              }}
            >
              Save Notes
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function Board() {
  const [columns, setColumns] = useState<Record<string, KanbanItem[]>>({});
  const [activeItem, setActiveItem] = useState<KanbanItem | null>(null);
  const [detailItem, setDetailItem] = useState<KanbanItem | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const load = useCallback(() => {
    api.getFavorites().then((data) => {
      const cols: Record<string, KanbanItem[]> = {};
      for (const col of COLUMNS) cols[col.id] = [];
      for (const [status, items] of Object.entries(data)) {
        if (cols[status]) cols[status] = items;
        else if (cols["new"]) cols["new"].push(...items);
      }
      setColumns(cols);
    });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const findItem = (postId: string): KanbanItem | undefined => {
    for (const items of Object.values(columns)) {
      const found = items.find((i) => i.post_id === postId);
      if (found) return found;
    }
  };

  const findColumn = (postId: string): string | undefined => {
    for (const [colId, items] of Object.entries(columns)) {
      if (items.some((i) => i.post_id === postId)) return colId;
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    const item = findItem(String(event.active.id));
    setActiveItem(item ?? null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveItem(null);
    const { active, over } = event;
    if (!over) return;

    const postId = String(active.id);
    const sourceCol = findColumn(postId);
    const targetCol = COLUMNS.some((c) => c.id === String(over.id))
      ? String(over.id)
      : findColumn(String(over.id));

    if (!sourceCol || !targetCol || sourceCol === targetCol) return;

    const item = findItem(postId);
    if (!item) return;

    setColumns((prev) => {
      const next = { ...prev };
      next[sourceCol] = prev[sourceCol].filter((i) => i.post_id !== postId);
      next[targetCol] = [...prev[targetCol], { ...item, kanban_status: targetCol }];
      return next;
    });

    api.updateFavorite(item.id, { kanban_status: targetCol });
  };

  const handleSaveNotes = async (item: KanbanItem, notes: string) => {
    await api.updateFavorite(item.id, { notes });
    load();
  };

  const handleRemove = async (item: KanbanItem) => {
    await api.removeFavorite(item.post_id);
    load();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Board</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Drag cards between columns to track your research
        </p>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <DroppableColumn
              key={col.id}
              id={col.id}
              label={col.label}
              items={columns[col.id] ?? []}
              onCardClick={setDetailItem}
              onRemove={handleRemove}
            />
          ))}
        </div>

        <DragOverlay>
          {activeItem ? <CardOverlay item={activeItem} /> : null}
        </DragOverlay>
      </DndContext>

      <DetailDialog
        item={detailItem}
        open={!!detailItem}
        onClose={() => setDetailItem(null)}
        onSaveNotes={handleSaveNotes}
      />
    </div>
  );
}
