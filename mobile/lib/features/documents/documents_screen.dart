import 'dart:io';

import 'package:flutter/material.dart';

import '../../api/mobile_backend.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({
    required this.controller,
    required this.backend,
    super.key,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  late Future<List<EmployeeMobileDocument>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ShellScaffold(
      title: l10n.documentsTitle,
      subtitle: l10n.documentsSubtitle,
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
        FutureBuilder<List<EmployeeMobileDocument>>(
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
                title: l10n.documentsErrorTitle,
                subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                icon: Icons.error_outline_rounded,
              );
            }
            final items = snapshot.data ?? const [];
            if (items.isEmpty) {
              return HighlightCard(
                title: l10n.documentsEmptyTitle,
                subtitle: l10n.documentsEmptySubtitle,
                icon: Icons.folder_off_rounded,
              );
            }
            return Column(
              children: items
                  .map(
                    (item) => Card(
                      margin: const EdgeInsets.only(bottom: 14),
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: Row(
                          children: [
                            Icon(Icons.description_outlined, color: Theme.of(context).colorScheme.primary),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(item.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                                  const SizedBox(height: 4),
                                  Text('${item.fileName ?? '-'} • ${item.relationType}'),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            if (item.scheduleDate != null) Chip(label: Text(_dateLabel(item.scheduleDate!))),
                            IconButton(
                              onPressed: () => _download(item),
                              icon: const Icon(Icons.download_rounded),
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

  Future<List<EmployeeMobileDocument>> _load() {
    return widget.controller.withAccessToken(widget.backend.fetchDocuments);
  }

  String _dateLabel(DateTime value) => '${value.day.toString().padLeft(2, '0')}.${value.month.toString().padLeft(2, '0')}';

  Future<void> _download(EmployeeMobileDocument item) async {
    final messenger = ScaffoldMessenger.of(context);
    if (item.currentVersionNo == null || item.fileName == null) {
      messenger.showSnackBar(SnackBar(content: Text(context.l10n.documentsDownloadUnavailable)));
      return;
    }
    final bytes = await widget.controller.withAccessToken(
      (token) => widget.backend.downloadOwnDocument(
        token,
        documentId: item.documentId,
        versionNo: item.currentVersionNo!,
      ),
    );
    final file = File('${Directory.systemTemp.path}/${item.fileName}');
    await file.writeAsBytes(bytes, flush: true);
    if (!mounted) {
      return;
    }
    messenger.showSnackBar(SnackBar(content: Text(context.l10n.documentsDownloaded(file.path))));
  }
}
