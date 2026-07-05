/**
 * The signature element of this app: a thin horizontal "ledger rail" per
 * category. It's a ruled line (like a paper ledger), filled to show actual
 * spend against planned, with a small tick marking how far into the month
 * we are. If the fill has already passed the tick, you're spending faster
 * than the month is passing -- that's the whole "pace" concept made visible
 * without needing a chart or a number to explain it.
 */
export default function LedgerRail({ planned, actual, pctElapsed, pace }) {
  const pct = planned > 0 ? Math.min((actual / planned) * 100, 100) : 0
  const overflow = planned > 0 && actual > planned

  const fillColor =
    pace === 'over_budget' ? 'bg-clay' : pace === 'ahead_of_pace' ? 'bg-turmeric' : 'bg-olive'

  return (
    <div className="relative h-[7px] w-full rounded-full bg-line overflow-visible">
      <div
        className={`h-full rounded-full ${fillColor} transition-[width] duration-500 ease-out`}
        style={{ width: `${pct}%` }}
      />
      {planned > 0 && pctElapsed > 0 && pctElapsed < 1 && (
        <div
          className="absolute top-1/2 -translate-y-1/2 w-[2px] h-[11px] bg-ink/40 rounded-full"
          style={{ left: `${pctElapsed * 100}%` }}
          title="Where the month is today"
        />
      )}
      {overflow && (
        <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-clay" />
      )}
    </div>
  )
}
