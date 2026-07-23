import PageContainer from '../components/common/PageContainer';
import HeroBanner from '../components/homepage/HeroBanner';
import TechFeatures from '../components/homepage/TechFeatures';
export default function HomePage() {
  return <PageContainer className="pt-0">
      <HeroBanner />
      <TechFeatures />
    </PageContainer>;
}
