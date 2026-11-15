import Scene from './scene/Scene';
import { AtlasProvider } from './state/AtlasContext';
import { Hero } from './ui/Hero';
import { TopBar } from './ui/TopBar';
import { MissionDirector } from './ui/MissionDirector';
import { Inspector } from './ui/Inspector';
import { DockTray } from './ui/DockTray';
import { Onboarding } from './ui/Onboarding';
import { RepoDrawer } from './ui/RepoDrawer';
import { Callout } from './ui/Callout';

export default function App() {
  return (
    <AtlasProvider>
      <div className="relative w-full h-full overflow-hidden bg-[#040609] select-none">
        <Scene />
        <div className="absolute inset-0 pointer-events-none">
          <Hero />
          <TopBar />
          <MissionDirector />
          <Inspector />
          <Callout />
          <DockTray />
        </div>
        <Onboarding />
        <RepoDrawer />
      </div>
    </AtlasProvider>
  );
}
