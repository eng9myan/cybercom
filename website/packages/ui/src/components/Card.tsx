import { type HTMLAttributes, forwardRef } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ hover = false, className = "", children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={[
          "bg-white/[0.04] border border-white/[0.08] backdrop-blur-md rounded-2xl",
          "shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_8px_32px_rgba(0,0,0,0.4)]",
          hover &&
            "transition-all duration-300 hover:bg-white/[0.08] hover:border-white/[0.12] hover:shadow-[0_0_0_1px_rgba(255,255,255,0.12),0_16px_48px_rgba(0,0,0,0.5)] cursor-pointer",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";
