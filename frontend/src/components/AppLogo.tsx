import Image from "next/image";
import { APP_NAME } from "@/config";

/** A component that shows the product logo: the spotlight mark and the product name. */
export function AppLogo() {
  return (
    <div className="flex items-center gap-3">
      <Image src="/logo.png" alt="" width={40} height={40} loading="eager" />
      <span className="text-[17px] font-extrabold tracking-[-0.01em]">{APP_NAME}</span>
    </div>
  );
}
