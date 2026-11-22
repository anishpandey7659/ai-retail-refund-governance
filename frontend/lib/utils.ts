export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function formatMoney(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(dateString: string): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function formatDateTime(dateString: string): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export const statusStyleMap: Record<
  string,
  { bg: string; text: string; border: string; label: string }
> = {
  Processing: {
    bg: "bg-[#FDF6E2]",
    text: "text-[#7A5B25]",
    border: "border-[#F0DC9B]",
    label: "Processing",
  },
  Shipped: {
    bg: "bg-[#EBF3E8]",
    text: "text-[#3D5B3F]",
    border: "border-[#D1E3CC]",
    label: "Shipped",
  },
  Delivered: {
    bg: "bg-[#EBF1F5]",
    text: "text-[#3B4B5A]",
    border: "border-[#D0DEE7]",
    label: "Delivered",
  },
  delivered: {
    bg: "bg-[#EBF1F5]",
    text: "text-[#3B4B5A]",
    border: "border-[#D0DEE7]",
    label: "Delivered",
  },
  pending: {
    bg: "bg-[#FDF6E2]",
    text: "text-[#7A5B25]",
    border: "border-[#F0DC9B]",
    label: "Pending",
  },
  Cancelled: {
    bg: "bg-[#F7EBE8]",
    text: "text-[#7A4039]",
    border: "border-[#E8C7C1]",
    label: "Cancelled",
  },
  "Not Requested": {
    bg: "bg-[#F3F1ED]",
    text: "text-[#6B6661]",
    border: "border-[#E2DED7]",
    label: "Not Requested",
  },
  "Pending Review": {
    bg: "bg-[#FAF1D6]",
    text: "text-[#75591F]",
    border: "border-[#EAD397]",
    label: "Pending Review",
  },
  Approved: {
    bg: "bg-[#DFEAE0]",
    text: "text-[#2D4E35]",
    border: "border-[#BED2C1]",
    label: "Approved",
  },
  Denied: {
    bg: "bg-[#EFD6D1]",
    text: "text-[#783D31]",
    border: "border-[#E1B8B0]",
    label: "Denied",
  },
  Refunded: {
    bg: "bg-[#DFEAE0]",
    text: "text-[#2D4E35]",
    border: "border-[#BED2C1]",
    label: "Refunded",
  },
  placed: {
    bg: "bg-[#FDF6E2]",
    text: "text-[#7A5B25]",
    border: "border-[#F0DC9B]",
    label: "Placed",
  },
  Paid: {
    bg: "bg-[#DFEAE0]",
    text: "text-[#2D4E35]",
    border: "border-[#BED2C1]",
    label: "Paid",
  },
  "In Transit": {
    bg: "bg-[#EBF3E8]",
    text: "text-[#3D5B3F]",
    border: "border-[#D1E3CC]",
    label: "In Transit",
  },
  Failed: {
    bg: "bg-[#EFD6D1]",
    text: "text-[#783D31]",
    border: "border-[#E1B8B0]",
    label: "Failed",
  },
};
