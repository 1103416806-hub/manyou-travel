# 慢游 · 西湖横幅配图

- 生成方式：内置 `image_gen__imagegen` 工具；单次生成，未使用 CLI 或 API 回退。
- 日期：2026-09-12。
- 用途：旅行规划工作台的意境配图；使用时标注“意境配图”，不代表实时天气、实地摄影或景点实况。
- 目标文件：`web/public/hangzhou-cover.png`。
- 画面检查：宽幅江南湖景，垂柳、小舟、层叠远山和亭檐；绿色与暖白色调；没有文字或界面元素。
- 建议展示：横幅可用 `object-fit: cover`，主体在中间偏下，按最终页面检查裁切。

## 实际生成提示词

```text
Use case: photorealistic-natural
Asset type: ultra-wide landscape banner for a Chinese short-city-trip planning workspace, named 慢游 MANYOU; generate scenery only, not a UI or mockup.
Primary request: an art-directed editorial travel photograph inspired by Hangzhou West Lake and the Jiangnan landscape: pale jade-green lake water, natural drooping willow branches in the foreground, one small traditional wooden boat in the middle distance, softly layered distant hills, and a restrained traditional pavilion roofline.
Style/medium: refined natural editorial photography with true-to-life textures and subtle film grain; serene, human warmth, tasteful and understated.
Composition/framing: very wide horizontal landscape, preferably around 1536x640 if available. Keep the key boat, shoreline, and distant hills within the central horizontal band so the image can be cropped to a 3.5:1 banner. Spacious lake surface; natural asymmetry and layered depth. No framing border.
Lighting/mood: gentle early-morning natural light, softly diffused atmosphere, delicate reflections and ripples, calm.
Color palette: muted pale jade and sage water, forest green willow leaves, warm off-white light; harmonious with forest-green and warm-white UI.
Constraints: no words, no text, no logo, no watermark, no map, no interface, no saturated bright blue or teal, no exaggerated fantasy architecture. This is an evocative generated scenic illustration, not a representation of live weather or real-time photography.
```

