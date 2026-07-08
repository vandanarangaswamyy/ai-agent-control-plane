import { ReactNode } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function StatCard({
  label,
  value,
  helpText,
  icon,
}: {
  label: string;
  value: string;
  helpText?: string;
  icon?: ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <CardDescription>{label}</CardDescription>
        {icon ? <div className="text-muted-foreground">{icon}</div> : null}
      </CardHeader>
      <CardContent>
        <CardTitle className="text-2xl">{value}</CardTitle>
        {helpText ? <p className="mt-1 text-xs text-muted-foreground">{helpText}</p> : null}
      </CardContent>
    </Card>
  );
}

