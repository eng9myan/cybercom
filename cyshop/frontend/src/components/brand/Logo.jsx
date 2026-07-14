import Link from 'next/link';

export default function Logo({ size = 32, mark = false, href = '/', className = '' }) {
  const inner = (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
        <defs>
          <linearGradient id="cy-grad" x1="0" y1="0" x2="48" y2="48">
            <stop offset="0%" stopColor="#ED6C00" />
            <stop offset="100%" stopColor="#FF8A2A" />
          </linearGradient>
        </defs>
        <path
          d="M40 24a16 16 0 1 1-8.5-14.1"
          stroke="url(#cy-grad)"
          strokeWidth="6"
          strokeLinecap="round"
          fill="none"
        />
        <circle cx="36" cy="14" r="4" fill="#59C3E1" />
      </svg>
      {!mark && (
        <span className="font-heading font-black tracking-tight text-[1.05rem] leading-none">
          Cy<span style={{ color: '#ED6C00' }}>shop</span>
        </span>
      )}
    </span>
  );
  return href ? <Link href={href} aria-label="Cyshop home">{inner}</Link> : inner;
}
