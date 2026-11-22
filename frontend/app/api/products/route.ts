import { NextRequest, NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/shop-api";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const targetUrl = `${API_BASE_URL}/products?${searchParams.toString()}`;

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

export async function POST(request: NextRequest) {
  const targetUrl = `${API_BASE_URL}/products`;

  try {
    const formData = await request.formData();
    const authorization = request.headers.get("authorization");

    const backendRes = await fetch(targetUrl, {
      method: "POST",
      headers: authorization ? { authorization } : undefined,
      body: formData,
    });

    if (!backendRes.ok) {
      const err = await backendRes.text();
      return NextResponse.json(
        { error: err || `FastAPI returned HTTP ${backendRes.status}` },
        { status: backendRes.status },
      );
    }

    const data = await backendRes.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      { error: `Failed to forward request to FastAPI backend: ${msg}` },
      { status: 502 },
    );
  }
}
