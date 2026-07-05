import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const PALETTE = ['#B9832A', '#5C7A4F', '#A24B3B', '#6B6656', '#8A7A5B', '#3F5C4A', '#7A5C3C', '#A67C52']

function currency(n) {
  return `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

export default function CategoryPie({ categories, totalIncome = 0 }) {
  const data = categories
    .filter((c) => c.actual_amount > 0)
    .map((c) => ({ name: c.category_name, value: c.actual_amount }))

  if (data.length === 0) {
    return <p className="text-sm text-subink italic">Nothing spent yet this month.</p>
  }

  const totalSpent = data.reduce((sum, d) => sum + d.value, 0)

  return (
    <div className="flex items-center gap-4 flex-wrap">
      <div className="w-40 h-40 shrink-0">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={2}
              label={({ value }) => `${((value / totalSpent) * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
            </Pie>
            <Tooltip
              formatter={(v) => [
                `${currency(v)} (${((v / totalSpent) * 100).toFixed(1)}% of spend${
                  totalIncome > 0 ? `, ${((v / totalIncome) * 100).toFixed(1)}% of income` : ''
                })`,
                '',
              ]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex-1 min-w-[180px] space-y-1.5">
        {data.map((d, i) => (
          <div key={d.name} className="flex items-center justify-between text-sm gap-3">
            <span className="flex items-center gap-2 text-subink min-w-0">
              <span className="w-2 h-2 rounded-sm shrink-0" style={{ background: PALETTE[i % PALETTE.length] }} />
              <span className="truncate">{d.name}</span>
            </span>
            <span className="font-mono text-ink shrink-0 text-right">
              {currency(d.value)}
              <span className="block text-[10px] text-subink">
                {((d.value / totalSpent) * 100).toFixed(1)}% of spend
                {totalIncome > 0 && ` · ${((d.value / totalIncome) * 100).toFixed(1)}% of income`}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
