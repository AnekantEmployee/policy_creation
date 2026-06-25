'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { profileApi } from '@/api/profile';
import { BotBubble, ChatGroup } from './ChatBubble';
import { ChatNavigation } from './ChatNavigation';
import toast from 'react-hot-toast';

interface Props { active: boolean; done: boolean; }

export const ChatAnalyzing: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const { orgDescription, orgWebsite, orgCountry, orgName, profile, setProfile, setSelectedFrameworks, setPhase, reset } = useWizardStore();

  useEffect(() => {
    if (!active) return;
    profileApi.analyze({ description: orgDescription, website: orgWebsite || undefined, country: orgCountry || undefined, name: orgName })
      .then((data) => {
        setProfile(data);
        const auto = data.recommended_frameworks.filter(f => f.relevance_score >= 0.7).map(f => f.id);
        setSelectedFrameworks(auto);
        setPhase('frameworks');
      })
      .catch((e) => {
        toast.error(`Analysis failed: ${e.message}`);
        setPhase('org_info');
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  const handleBack = () => setPhase('org_info');
  const handleExit = () => {
    reset();
    router.push('/');
  };

  if (done) {
    return (
      <ChatGroup>
        <BotBubble done>
          ✅ Analysis complete — <strong>{profile?.org_type ?? 'Organization'}</strong> detected.
          {profile?.industries_detected?.length ? ` Industries: ${profile.industries_detected.join(', ')}.` : ''}
        </BotBubble>
        {active && (
          <ChatNavigation
            onBack={handleBack}
            onExit={handleExit}
            canGoBack={true}
          />
        )}
      </ChatGroup>
    );
  }

  return (
    <ChatGroup>
      <BotBubble>
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            {[0,1,2].map(i => (
              <span key={i} className="h-2 w-2 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
          <span>AI agents analyzing your organization and identifying applicable compliance frameworks…</span>
        </div>
      </BotBubble>
    </ChatGroup>
  );
};
