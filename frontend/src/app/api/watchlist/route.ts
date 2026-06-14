import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// GET /api/watchlist — fetch current user's watchlist
export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const entries = await prisma.watchlistEntry.findMany({
    where: { userId: session.user.id },
    orderBy: { addedAt: "desc" },
  });

  return NextResponse.json({ watchlist: entries });
}

// POST /api/watchlist — add a fund to watchlist
export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const { schemeCode, schemeName, category, sipAmount } = body;

  if (!schemeCode || !schemeName || !category) {
    return NextResponse.json(
      { error: "Missing required fields" },
      { status: 400 },
    );
  }

  try {
    const entry = await prisma.watchlistEntry.upsert({
      where: {
        userId_schemeCode: {
          userId: session.user.id,
          schemeCode,
        },
      },
      update: { sipAmount: sipAmount ?? 0 },
      create: {
        userId: session.user.id,
        schemeCode,
        schemeName,
        category,
        sipAmount: sipAmount ?? 0,
        sipStartDate: new Date(),
      },
    });

    return NextResponse.json({ entry }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Failed to save" }, { status: 500 });
  }
}
