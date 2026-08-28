import type { ReactNode } from "react";

type Props = {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
  children: ReactNode;
};

export function Field({ label, required, hint, error, children }: Props) {
  return (
    <div className="mb-4">
      <label className="block">
        <span className="mb-1.5 block text-sm font-medium text-ink">
          {label}
          {required && <span className="text-danger"> *</span>}
        </span>
        {children}
      </label>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
      {error && (
        <p className="mt-1 text-xs text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
