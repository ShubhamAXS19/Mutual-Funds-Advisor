"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { NavPoint } from "@/types";

interface Props {
  data: NavPoint[];
  color?: string;
}

function formatDate(dateStr: string): string {
  // MFAPI returns DD-MM-YYYY
  const parts = dateStr.split("-");
  if (parts.length !== 3) return dateStr;
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const month = months[parseInt(parts[1]) - 1];
  return `${month} '${parts[2].slice(2)}`;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-100 shadow-sm rounded-lg px-3 py-2 text-xs">
        <p className="text-gray-500">{label}</p>
        <p className="font-semibold text-gray-800">
          ₹{payload[0].value.toFixed(2)}
        </p>
      </div>
    );
  }
  return null;
};

export default function NavChart({ data, color = "#6366f1" }: Props) {
  // Sample every ~5 points to keep chart performant (252 → ~50 points)
  const sampled = data.filter((_, i) => i % 5 === 0);

  const formatted = sampled.map((p) => ({
    date: formatDate(p.date),
    nav: p.nav,
  }));

  const minNav = Math.min(...formatted.map((p) => p.nav)) * 0.97;
  const maxNav = Math.max(...formatted.map((p) => p.nav)) * 1.01;

  return (
    <ResponsiveContainer width="100%" height={120}>
      <AreaChart
        data={formatted}
        margin={{ top: 4, right: 4, left: 0, bottom: 0 }}
      >
        <defs>
          <linearGradient
            id={`grad-${color.replace("#", "")}`}
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop offset="5%" stopColor={color} stopOpacity={0.15} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: "#9ca3af" }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis domain={[minNav, maxNav]} hide />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="nav"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#grad-${color.replace("#", "")})`}
          dot={false}
          activeDot={{ r: 3, fill: color }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
