import type {CityStoryContent} from './city-story-contract.ts';

/** First-playable story copy. Narrative-owned; runtime reads this object only. */
export const CITY_STORY_CONTENT: CityStoryContent = {
  schemaVersion: 1,
  id: 'bay-last-delivery',
  title: '最后一单',
  synopsis:
    '收工前，阿辉把环岛路那单的保温袋交给你。先去五缘湾商务驿站让阿琳核销，再决定直接送环岛路交接点，还是绕白鹭洲养护站把卡箍给老陈。',
  firstStep: 'hub-pickup',
  reward: 180,
  people: {
    ahui: {name: '阿辉', role: '驿站日结，本单派件'},
    alin: {name: '阿琳', role: '五缘湾职场人，本单核销'},
    laochen: {name: '老陈', role: '城市工人，本单在白鹭洲养护站等卡箍'},
    player: {name: '你', role: '日结配送'},
  },
  steps: [
    {
      id: 'hub-pickup',
      place: 'hub',
      title: '驿站还不能关',
      objective: '到会展生活驿站停稳下车，向阿辉领取保温袋。',
      action: 'collect',
      lines: [
        {speaker: 'ahui', text: '环岛路那单还搁着，晚班退件没到，我走不开。'},
        {speaker: 'ahui', text: '保温袋给你。先去五缘湾驿站让阿琳对码，再送环岛路。'},
      ],
      next: 'office-meet',
    },
    {
      id: 'office-meet',
      place: 'office',
      title: '窗口对码',
      objective: '到五缘湾商务驿站门前停稳下车，找阿琳核对取件码。',
      action: 'talk',
      lines: [
        {speaker: 'alin', text: '码对上了。工作群催我回去，我得先走。'},
        {speaker: 'alin', text: '老陈的卡箍还在我包里。你先送环岛路，还是顺路丢白鹭洲？'},
      ],
      choices: [
        {
          id: 'go-bay-direct',
          label: '先去环岛路交接点交货',
          next: 'bay-direct',
          consequence: '不去白鹭洲。阿琳回公司，卡箍留在五缘湾商务驿站，老陈明早来取；下一站环岛路边交接点。',
        },
        {
          id: 'detour-park',
          label: '先去白鹭洲养护站把卡箍给老陈',
          next: 'office-spare',
          consequence: '仍在五缘湾商务驿站向阿琳取走卡箍，再去白鹭洲养护站，最后送环岛路交接点。',
        },
      ],
    },
    {
      id: 'office-spare',
      place: 'office',
      title: '包里的卡箍',
      objective: '在五缘湾商务驿站窗口停稳下车，向阿琳取走老陈的卡箍。',
      action: 'collect',
      lines: [
        {speaker: 'alin', text: '给，中午我签的。'},
        {speaker: 'alin', text: '拿着就走，我回公司了。'},
      ],
      next: 'park-help',
    },
    {
      id: 'park-help',
      place: 'park',
      title: '养护站交接',
      objective: '到白鹭洲养护站停稳下车，把卡箍交给老陈。',
      action: 'deliver',
      lines: [
        {speaker: 'laochen', text: '卡箍来了就行，今晚不换过道筼筜湖畔要积水。'},
        {speaker: 'laochen', text: '环岛路那袋还等着，你走。'},
      ],
      next: 'bay-after-park',
    },
    {
      id: 'bay-direct',
      place: 'bay',
      title: '趁热送到',
      objective: '到环岛路边交接点停稳下车，交付保温袋。',
      action: 'deliver',
      lines: [
        {speaker: 'ahui', text: '对面回了，饭烫手，签收了。'},
        {speaker: 'ahui', text: '你回会展驿站结。'},
      ],
      next: 'hub-end-direct',
    },
    {
      id: 'bay-after-park',
      place: 'bay',
      title: '送到，但温了',
      objective: '到环岛路边交接点停稳下车，交付保温袋。',
      action: 'deliver',
      lines: [
        {speaker: 'ahui', text: '签是签了，说不烫了。'},
        {speaker: 'ahui', text: '钱照结，你回来。'},
      ],
      next: 'hub-end-detour',
    },
    {
      id: 'hub-end-direct',
      place: 'hub',
      title: '准时收工',
      objective: '回会展生活驿站停稳下车，找阿辉结算。',
      action: 'talk',
      lines: [
        {speaker: 'ahui', text: '换班前送到，一百八打你账上。'},
        {speaker: 'ahui', text: '老陈问卡箍，他说明早自己来五缘湾驿站取。'},
      ],
      terminal: true,
    },
    {
      id: 'hub-end-detour',
      place: 'hub',
      title: '单子还是结了',
      objective: '回会展生活驿站停稳下车，找阿辉结算。',
      action: 'talk',
      lines: [
        {speaker: 'ahui', text: '饭温了他们也收，一百八不少你的。'},
        {speaker: 'ahui', text: '老陈对讲里谢了声。下次零件走维修站，别绕配送单。'},
      ],
      terminal: true,
    },
  ],
};
