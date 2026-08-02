# flatpak-repo

`dart-flutter-demo` 的自建、GPG 签名 Flatpak 更新仓库。

- 应用 ID：`io.github.vincentzyuapps.dartflutterdemo`
- 架构：`x86_64`
- 更新通道：`stable`
- 页面：<https://vincentzyuapps.github.io/flatpak-repo/>
- 应用源码：<https://github.com/VincentZyuApps/dart-flutter-demo>
- GPG 指纹：`34DA05F98B42968BCCCDDF1B35831D1AE820C955`

## 安装

首次发布完成后，可以直接安装固定的 `.flatpakref`：

```bash
flatpak install --user https://vincentzyuapps.github.io/flatpak-repo/dart-flutter-demo.flatpakref
flatpak run io.github.vincentzyuapps.dartflutterdemo
```

也可以先添加仓库，再安装应用：

```bash
flatpak remote-add --user --if-not-exists dart-flutter-demo \
  https://vincentzyuapps.github.io/flatpak-repo/dart-flutter-demo.flatpakrepo
flatpak install --user dart-flutter-demo io.github.vincentzyuapps.dartflutterdemo
```

后续更新使用：

```bash
flatpak update --user io.github.vincentzyuapps.dartflutterdemo
```

## 发布模型

`main` 分支只保存工作流、公开公钥、渲染脚本和文档。`repo-state` 分支由 GitHub Actions 维护，持久保存生成的 OSTree 仓库、静态 delta、`.flatpakref` 和 `.flatpakrepo`。

应用仓库中的 `[build-publish]` 会先创建完整 GitHub Release，再向本仓库推送 `publish-v<version>` 标签。标签触发的工作流从 Release 下载版本化 `.flatpak`，验证身份和分支，使用 `flatpak-production` Environment 中的 GPG 密钥签名，并通过 GitHub Pages 部署。

私钥和口令不得提交到任何分支、Artifact、Pages 或日志。公开公钥位于 [`keys/flatpak-repo-signing-public.asc`](keys/flatpak-repo-signing-public.asc)。
