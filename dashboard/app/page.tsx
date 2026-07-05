import { Hero } from "@/components/landing/Hero";
import { Problem } from "@/components/landing/Problem";
import { Solution } from "@/components/landing/Solution";
import { TechEcosystem } from "@/components/landing/TechEcosystem";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ProductPreview } from "@/components/landing/ProductPreview";
import { Trust } from "@/components/landing/Trust";
import { CTAStrip } from "@/components/landing/CTAStrip";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";

export default function Home() {
  return (
    <>
      <Nav />
      <main className="flex-1">
        <Hero />
        <Problem />
        <Solution />
        <TechEcosystem />
        <HowItWorks />
        <ProductPreview />
        <Trust />
        <CTAStrip />
      </main>
      <Footer />
    </>
  );
}
