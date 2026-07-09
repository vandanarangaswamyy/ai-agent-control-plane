import { Inbox } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function EmptyState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center gap-3 py-10 text-center">
        <div className="rounded-full bg-muted p-3 text-muted-foreground">
          <Inbox className="h-5 w-5" />
        </div>
        <div className="space-y-1">
          <p className="font-medium">{title}</p>
          <p className="max-w-md text-sm text-muted-foreground">{message}</p>
          <p className="text-xs text-muted-foreground">
            Seed demo data to populate this view and keep the dashboard active.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
