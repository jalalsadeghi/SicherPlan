import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../api/mobile_backend.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class InfoFeedScreen extends StatefulWidget {
  const InfoFeedScreen({
    required this.controller,
    required this.backend,
    super.key,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;

  @override
  State<InfoFeedScreen> createState() => _InfoFeedScreenState();
}

class _InfoFeedScreenState extends State<InfoFeedScreen> {
  late Future<List<NoticeItem>> _future;
  NoticeFeedStatus? _status;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ShellScaffold(
      title: l10n.feedTitle,
      subtitle: l10n.feedSubtitle,
      actions: [
        IconButton(
          onPressed: () {
            setState(() {
              _future = _load();
            });
          },
          icon: const Icon(Icons.refresh_rounded),
        ),
      ],
      children: [
        if (_status != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: HighlightCard(
              title: l10n.feedTitle,
              subtitle: '${_status!.unreadCount} / ${_status!.totalCount}',
              icon: Icons.campaign_outlined,
            ),
          ),
        FutureBuilder<List<NoticeItem>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Center(child: CircularProgressIndicator()),
              );
            }
            if (snapshot.hasError) {
              return HighlightCard(
                title: l10n.feedErrorTitle,
                subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                icon: Icons.error_outline_rounded,
              );
            }
            final notices = snapshot.data ?? const [];
            if (notices.isEmpty) {
              return HighlightCard(
                title: l10n.feedEmptyTitle,
                subtitle: l10n.feedEmptySubtitle,
                icon: Icons.notifications_off_outlined,
              );
            }
            return Column(
              children: notices
                  .map(
                    (notice) => Card(
                      margin: const EdgeInsets.only(bottom: 14),
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  notice.mandatoryAcknowledgement
                                      ? Icons.announcement_outlined
                                      : Icons.notifications_active_outlined,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    notice.title,
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleMedium
                                        ?.copyWith(fontWeight: FontWeight.w700),
                                  ),
                                ),
                                Chip(
                                  label: Text(
                                    notice.acknowledgedAt != null
                                        ? l10n.noticeAcknowledgedBadge
                                        : l10n.noticeUnreadBadge,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(notice.summary ?? '-'),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 8,
                              children: [
                                TextButton(
                                  onPressed: () => _openNotice(notice),
                                  child: Text(l10n.noticeOpenAction),
                                ),
                                if (notice.mandatoryAcknowledgement &&
                                    notice.acknowledgedAt == null)
                                  FilledButton.tonal(
                                    onPressed: () => _acknowledgeNotice(notice),
                                    child: Text(l10n.noticeAcknowledgeAction),
                                  ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  )
                  .toList(),
            );
          },
        ),
      ],
    );
  }

  Future<List<NoticeItem>> _load() {
    final tenantId = widget.controller.context?.tenantId ?? '';
    return widget.controller.withAccessToken((token) async {
      _status = await widget.backend.fetchNoticeFeedStatus(token, tenantId);
      return widget.backend.fetchNotices(token, tenantId);
    });
  }

  Future<void> _openNotice(NoticeItem notice) async {
    final tenantId = widget.controller.context?.tenantId ?? '';
    final opened = await widget.controller.withAccessToken((token) async {
      await widget.backend.openNotice(token, tenantId, notice.id);
      return widget.backend.fetchNotice(token, tenantId, notice.id);
    });
    if (!mounted) {
      return;
    }
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        final theme = Theme.of(context);
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(opened.title, style: theme.textTheme.titleLarge),
                const SizedBox(height: 12),
                Text(opened.body ?? opened.summary ?? opened.status),
                const SizedBox(height: 12),
                if (opened.links.isNotEmpty)
                  Wrap(
                    spacing: 8,
                    children: opened.links
                        .map(
                          (link) => ActionChip(
                            label: Text(link.label),
                            onPressed: () => Clipboard.setData(
                              ClipboardData(text: link.url),
                            ),
                          ),
                        )
                        .toList(),
                  ),
                if (opened.attachments.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    children: opened.attachments
                        .where(
                          (attachment) => attachment.currentVersionNo != null,
                        )
                        .map(
                          (attachment) => ActionChip(
                            label: Text(
                              attachment.fileName ?? attachment.title,
                            ),
                            onPressed: () => _downloadAttachment(attachment),
                          ),
                        )
                        .toList(),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
    if (!mounted) {
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    final l10n = context.l10n;
    messenger.showSnackBar(SnackBar(content: Text(l10n.noticeOpened)));
    setState(() {
      _future = _load();
    });
  }

  Future<void> _acknowledgeNotice(NoticeItem notice) async {
    final tenantId = widget.controller.context?.tenantId ?? '';
    await widget.controller.withAccessToken(
      (token) => widget.backend.acknowledgeNotice(token, tenantId, notice.id),
    );
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(context.l10n.noticeAcknowledgedDone)),
    );
    setState(() {
      _future = _load();
    });
  }

  Future<void> _downloadAttachment(NoticeAttachmentItem attachment) async {
    final tenantId = widget.controller.context?.tenantId ?? '';
    await widget.controller.withAccessToken(
      (token) => widget.backend.downloadNoticeAttachment(
        token,
        tenantId: tenantId,
        documentId: attachment.documentId,
        versionNo: attachment.currentVersionNo ?? 1,
      ),
    );
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(attachment.fileName ?? attachment.title)),
    );
  }
}
