import { Loader2 } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function LoadingState({ label = "Loading data" }: { label?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-8">
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}

