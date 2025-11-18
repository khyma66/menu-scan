"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import DeliveryAppHome from "@/components/DeliveryAppHome";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to enhanced delivery app which has the doordash-like UI
    router.push("/enhanced-delivery");
  }, [router]);

  // Show the delivery app directly while redirecting
  return (
    <div className="min-h-screen bg-gray-50">
      <DeliveryAppHome />
    </div>
  );
}
