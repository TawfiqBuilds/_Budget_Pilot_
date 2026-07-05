/**
 * Matches the "stamp" motif from the existing app -- a rotated, bordered
 * label, like a rubber stamp on a paper receipt. Used for FIXED / ARCHIVED tags.
 */
export default function Stamp({ children, color = '#6B6656' }) {
  return (
    <span
      className="inline-block font-mono text-[9.5px] font-bold uppercase tracking-wider border-2 rounded px-1.5 py-0.5 -rotate-6"
      style={{ color, borderColor: color }}
    >
      {children}
    </span>
  )
}
