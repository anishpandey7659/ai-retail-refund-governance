import { NextRequest, NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/shop-api";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const targetUrl = `${API_BASE_URL}/products/${id}`;

  try {
    const backendRes = await fetch(targetUrl, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!backendRes.ok) {
      const err = await backendRes.text();
      return NextResponse.json(
        { error: err || `FastAPI returned HTTP ${backendRes.status}` },
        { status: backendRes.status },
      );
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      { error: `Failed to connect to FastAPI backend: ${msg}` },
      { status: 502 },
    );
  }
}
