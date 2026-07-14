import { type InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", id, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={id}
            className="block text-sm font-medium text-[#e2e8f0] mb-1.5"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={[
            "w-full px-4 py-3 rounded-xl bg-white/[0.04] border text-white placeholder:text-[#475569] text-sm transition-all duration-200",
            "focus:outline-none focus:border-[#ED6C00]/50 focus:ring-1 focus:ring-[#ED6C00]/30",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            error
              ? "border-red-500/50"
              : "border-white/[0.08]",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
          aria-invalid={!!error}
          aria-describedby={error && id ? `${id}-error` : undefined}
          {...props}
        />
        {error && (
          <p
            id={id ? `${id}-error` : undefined}
            className="mt-1.5 text-xs text-red-400 flex items-center gap-1"
            role="alert"
          >
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
