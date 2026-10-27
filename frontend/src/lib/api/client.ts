const PREFIX = "/api/v1";

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(PREFIX + path, {
    ...options,
    headers: options.body instanceof FormData ? options.headers : {
      "Content-Type": "application/json", ...options.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Không thể kết nối máy chủ." }));
    throw new Error(typeof error.detail === "string" ? error.detail : "Dữ liệu chưa hợp lệ. Kiểm tra các trường nhập.");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Không thể hoàn thành thao tác.";
}
