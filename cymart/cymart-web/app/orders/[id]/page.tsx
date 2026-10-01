import { TrackingView } from "@/components/TrackingView";

export default async function OrderTrackingPage({ params }: PageProps<"/orders/[id]">) {
  const { id } = await params;
  return <TrackingView orderId={id} />;
}
