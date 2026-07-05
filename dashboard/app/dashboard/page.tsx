import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { SidebarNav } from "@/components/dashboard/SidebarNav";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { StatusCards } from "@/components/dashboard/StatusCards";
import { CorrelationPanel } from "@/components/dashboard/CorrelationPanel";
import { ActivityTimeline } from "@/components/dashboard/ActivityTimeline";
import { DriftChart } from "@/components/dashboard/DriftChart";
import { TriggerPanel } from "@/components/dashboard/TriggerPanel";
import { MemoryPanel } from "@/components/dashboard/MemoryPanel";

export default function DashboardPage() {
  return (
    <>
      <Nav trail="Dashboard" />
      <main className="flex-1">
        <div className="mx-auto max-w-[1440px] px-6 lg:px-10">
          <div className="lg:grid lg:grid-cols-[230px_1fr] lg:gap-10">
            <SidebarNav />  

            <div className="min-w-0 py-10">
              <section id="overview" className="scroll-mt-32">
                <DashboardHeader />
                <div className="mt-10">
                  <StatusCards />
                </div>
              </section>

              <section
                id="memory"
                className="mt-16 scroll-mt-32 border-t border-line pt-12"
              >
                <MemoryPanel />
              </section>

              <section
                id="correlation"
                className="mt-16 scroll-mt-32 border-t border-line pt-12"
              >
                <CorrelationPanel />
              </section>

              <section
                id="timeline"
                className="mt-16 scroll-mt-32 border-t border-line pt-12"
              >
                <ActivityTimeline />
              </section>

              <section
                id="quality"
                className="mt-16 scroll-mt-32 border-t border-line pt-12"
              >
                <DriftChart />
              </section>

              <section
                id="triggers"
                className="mt-16 scroll-mt-32 border-t border-line pt-12 pb-6"
              >
                <TriggerPanel />
              </section>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
