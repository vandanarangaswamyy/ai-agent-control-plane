import { AlertTriangle, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ErrorState({
  title = "Failed to load data",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-8">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-destructive/10 p-2 text-destructive">
            <AlertTriangle className="h-4 w-4" />
          </div>
          <div>
            <p className="font-medium">{title}</p>
            <p className="text-sm text-muted-foreground">{message}</p>
          </div>
        </div>
        {onRetry ? (
          <div>
            <Button variant="outline" onClick={onRetry}>
              <RefreshCw className="h-4 w-4" />
              Retry
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

