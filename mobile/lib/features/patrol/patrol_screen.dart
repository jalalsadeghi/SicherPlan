import 'dart:convert';

import 'package:flutter/material.dart';

import '../../api/mobile_backend.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';
import 'patrol_controller.dart';
import 'patrol_store.dart';

class PatrolScreen extends StatefulWidget {
  const PatrolScreen({
    required this.controller,
    required this.backend,
    super.key,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;

  @override
  State<PatrolScreen> createState() => _PatrolScreenState();
}

class _PatrolScreenState extends State<PatrolScreen> {
  late final PatrolController _patrolController;
  final TextEditingController _tokenController = TextEditingController();
  final TextEditingController _noteController = TextEditingController();
  final TextEditingController _abortReasonController = TextEditingController(
    text: 'manual_stop',
  );
  String _scanMethodCode = 'qr';

  @override
  void initState() {
    super.initState();
    _patrolController = PatrolController(
      backend: widget.backend,
      store: FilePatrolOfflineStore(),
      withAccessToken: widget.controller.withAccessToken,
    )..load();
  }

  @override
  void dispose() {
    _tokenController.dispose();
    _noteController.dispose();
    _abortReasonController.dispose();
    _patrolController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return AnimatedBuilder(
      animation: _patrolController,
      builder: (context, _) {
        return ShellScaffold(
          title: l10n.patrolTitle,
          subtitle: l10n.patrolSubtitle,
          actions: [
            IconButton(
              onPressed: _patrolController.loading
                  ? null
                  : _patrolController.load,
              icon: const Icon(Icons.refresh_rounded),
            ),
            IconButton(
              onPressed: _patrolController.syncing
                  ? null
                  : _patrolController.sync,
              icon: const Icon(Icons.sync_rounded),
            ),
          ],
          children: [
            HighlightCard(
              title: l10n.patrolAccessTitle(
                widget.controller.context?.hasPatrolAccess ?? false,
              ),
              subtitle: l10n.patrolAccessSubtitle(
                widget.controller.context?.hasPatrolAccess ?? false,
              ),
              icon: Icons.shield_outlined,
              badge: _patrolController.pendingOperationCount > 0
                  ? l10n.patrolQueuedBadge(
                      _patrolController.pendingOperationCount,
                    )
                  : l10n.patrolAccessBadge(
                      widget.controller.context?.hasPatrolAccess ?? false,
                    ),
            ),
            if (_patrolController.messageKey != null)
              HighlightCard(
                title: l10n.patrolErrorTitle,
                subtitle: l10n.backendMessage(_patrolController.messageKey!),
                icon: Icons.error_outline_rounded,
              ),
            if (_patrolController.loading)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_patrolController.activeRound != null)
              _buildActiveRound(context)
            else
              _buildAvailableRoutes(context),
          ],
        );
      },
    );
  }

  Widget _buildAvailableRoutes(BuildContext context) {
    final l10n = context.l10n;
    final routes = _patrolController.routes;
    if (routes.isEmpty) {
      return HighlightCard(
        title: l10n.patrolEmptyTitle,
        subtitle: l10n.patrolEmptySubtitle,
        icon: Icons.route_outlined,
      );
    }
    return Column(
      children: routes
          .map(
            (route) => Card(
              margin: const EdgeInsets.only(bottom: 14),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${route.routeNo} · ${route.routeName}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(route.locationLabel ?? route.meetingPoint ?? '-'),
                    const SizedBox(height: 6),
                    Text(
                      '${route.checkpointCount} ${l10n.patrolCheckpointCountLabel}',
                    ),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: () => _patrolController.startRound(route),
                      icon: const Icon(Icons.play_arrow_rounded),
                      label: Text(l10n.patrolStartAction),
                    ),
                  ],
                ),
              ),
            ),
          )
          .toList(),
    );
  }

  Widget _buildActiveRound(BuildContext context) {
    final l10n = context.l10n;
    final round = _patrolController.activeRound!;
    final route = _patrolController.activeRoute;
    final evaluation = _patrolController.evaluation;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          margin: const EdgeInsets.only(bottom: 14),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  route == null
                      ? l10n.patrolInProgressTitle
                      : '${route.routeNo} · ${route.routeName}',
                  style: Theme.of(
                    context,
                  ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                Text(
                  '${round.completedCheckpointCount}/${round.totalCheckpointCount} ${l10n.patrolCheckpointCountLabel}',
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    Chip(
                      label: Text(
                        l10n.patrolStatusLabel(round.roundStatusCode),
                      ),
                    ),
                    if (_patrolController.pendingOperationCount > 0)
                      Chip(
                        label: Text(
                          l10n.patrolQueuedBadge(
                            _patrolController.pendingOperationCount,
                          ),
                        ),
                      ),
                  ],
                ),
                if (evaluation != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    l10n.patrolEvaluationTitle,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    l10n.patrolEvaluationSummary(
                      evaluation.complianceStatusCode,
                      evaluation.exceptionCount,
                      evaluation.manualCaptureCount,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
        Card(
          margin: const EdgeInsets.only(bottom: 14),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.patrolCaptureTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: _scanMethodCode,
                  decoration: InputDecoration(
                    labelText: l10n.patrolScanMethodLabel,
                  ),
                  items: const [
                    DropdownMenuItem(value: 'qr', child: Text('QR')),
                    DropdownMenuItem(value: 'barcode', child: Text('Barcode')),
                    DropdownMenuItem(value: 'nfc', child: Text('NFC')),
                    DropdownMenuItem(value: 'manual', child: Text('Manual')),
                  ],
                  onChanged: (value) {
                    if (value == null) return;
                    setState(() {
                      _scanMethodCode = value;
                    });
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _tokenController,
                  decoration: InputDecoration(labelText: l10n.patrolTokenLabel),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _noteController,
                  maxLines: 3,
                  decoration: InputDecoration(labelText: l10n.patrolNoteLabel),
                ),
              ],
            ),
          ),
        ),
        ...round.checkpoints.map(
          (checkpoint) => Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              title: Text('${checkpoint.sequenceNo}. ${checkpoint.label}'),
              subtitle: Text(
                '${checkpoint.checkpointCode} · ${checkpoint.scanTypeCode}',
              ),
              trailing: checkpoint.isCompleted
                  ? Chip(label: Text(l10n.patrolCheckpointDone))
                  : FilledButton.tonal(
                      onPressed: round.roundStatusCode == 'active'
                          ? () => _captureCheckpoint(checkpoint)
                          : null,
                      child: Text(l10n.patrolCaptureAction),
                    ),
            ),
          ),
        ),
        if (round.roundStatusCode == 'active')
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _abortReasonController,
                    decoration: InputDecoration(
                      labelText: l10n.patrolAbortReasonLabel,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      FilledButton.icon(
                        onPressed: _patrolController.syncing
                            ? null
                            : () => _patrolController.completeRound(
                                note: _noteController.text.trim().isEmpty
                                    ? null
                                    : _noteController.text.trim(),
                              ),
                        icon: const Icon(Icons.check_circle_outline_rounded),
                        label: Text(l10n.patrolCompleteAction),
                      ),
                      FilledButton.tonalIcon(
                        onPressed: _patrolController.syncing
                            ? null
                            : _abortRound,
                        icon: const Icon(Icons.cancel_outlined),
                        label: Text(l10n.patrolAbortAction),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }

  Future<void> _captureCheckpoint(
    PatrolCheckpointProgressItem checkpoint,
  ) async {
    final attachments =
        _scanMethodCode == 'manual' && _noteController.text.trim().isNotEmpty
        ? [
            PatrolEvidenceAttachmentPayload(
              title: 'manual-note',
              fileName: 'manual-note.txt',
              contentType: 'text/plain',
              contentBase64: base64Encode(
                utf8.encode(_noteController.text.trim()),
              ),
            ),
          ]
        : const <PatrolEvidenceAttachmentPayload>[];
    await _patrolController.captureCheckpoint(
      checkpoint: checkpoint,
      scanMethodCode: _scanMethodCode,
      tokenValue: _tokenController.text.trim().isEmpty
          ? null
          : _tokenController.text.trim(),
      note: _noteController.text.trim().isEmpty
          ? null
          : _noteController.text.trim(),
      reasonCode: _scanMethodCode == 'manual' ? 'manual_fallback' : null,
      attachments: attachments,
    );
    _tokenController.clear();
    _noteController.clear();
  }

  Future<void> _abortRound() async {
    final note = _noteController.text.trim();
    final attachments = note.isEmpty
        ? const <PatrolEvidenceAttachmentPayload>[]
        : [
            PatrolEvidenceAttachmentPayload(
              title: 'abort-note',
              fileName: 'abort-note.txt',
              contentType: 'text/plain',
              contentBase64: base64Encode(utf8.encode(note)),
            ),
          ];
    await _patrolController.abortRound(
      abortReasonCode: _abortReasonController.text.trim().isEmpty
          ? 'manual_stop'
          : _abortReasonController.text.trim(),
      note: note.isEmpty ? null : note,
      attachments: attachments,
    );
    _noteController.clear();
  }
}
