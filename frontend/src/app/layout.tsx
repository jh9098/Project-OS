import "@/app/globals.css";
import Providers from "@/app/providers";

export const metadata = {
  title: "Project OS",
  description: "개인용 프로젝트 운영실"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
