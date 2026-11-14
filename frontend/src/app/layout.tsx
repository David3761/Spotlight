import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import { APP_NAME } from "@/config";
import "./globals.css";

/** The app's only typeface, loaded as a variable font with Romanian diacritics. */
const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["latin", "latin-ext"],
});

/** The document metadata shared by every page. */
export const metadata: Metadata = {
  title: APP_NAME,
  description: "Te ajut să apari în recomandările lui Gemini",
};

/** The root layout: Romanian document, app font and page background. */
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ro" className={`${plusJakarta.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">{children}</body>
    </html>
  );
}
