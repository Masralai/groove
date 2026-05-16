import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Chat - Groove",
  description: "Natural language interface for querying your Meta Ads data with plain English questions.",
};

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}