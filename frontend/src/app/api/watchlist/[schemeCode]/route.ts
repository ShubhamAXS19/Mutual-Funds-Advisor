import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// DELETE /api/watchlist/:schemeCode
export async function DELETE(
  req: NextRequest,
  { params }: { params: { schemeCode: string } },
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    await prisma.watchlistEntry.delete({
      where: {
        userId_schemeCode: {
          userId: session.user.id,
          schemeCode: params.schemeCode,
        },
      },
    });

    return NextResponse.json({ deleted: true });
  } catch {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
}
