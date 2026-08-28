import type { ReactNode } from "react";

type Props = {
  kind?: "error" | "info" | "success";
  children: ReactNode;
};

export function Alert({ kind = "error", children }: Props) {
  const styles = {
    error: "border-danger/30 bg-danger/5 text-danger",
    info: "border-line bg-line/30 text-ink",
    success: "border-ok/30 bg-ok/5 text-ok",
  } as const;
  return (
    <div className={`rounded-xl border px-4 py-3 text-sm ${styles[kind]}`} role="status">
      {children}
    </div>
  );
}
