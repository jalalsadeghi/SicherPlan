import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../api/mobile_backend.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({
    required this.controller,
    required this.backend,
    super.key,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  late Future<List<EmployeeReleasedScheduleItem>> _schedulesFuture;
  late Future<List<EmployeeEventApplicationItem>> _applicationsFuture;
  final _planningRecordController = TextEditingController();
  final _applicationNoteController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _schedulesFuture = _loadSchedules();
    _applicationsFuture = _loadApplications();
  }

  @override
  void dispose() {
    _planningRecordController.dispose();
    _applicationNoteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ShellScaffold(
      title: l10n.scheduleTitle,
      subtitle: l10n.scheduleSubtitle,
      actions: [
        IconButton(
          onPressed: _refresh,
          icon: const Icon(Icons.refresh_rounded),
        ),
      ],
      children: [
        FutureBuilder<List<EmployeeReleasedScheduleItem>>(
          future: _schedulesFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Center(child: CircularProgressIndicator()),
              );
            }
            if (snapshot.hasError) {
              return HighlightCard(
                title: l10n.scheduleErrorTitle,
                subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                icon: Icons.error_outline_rounded,
              );
            }
            final schedules = snapshot.data ?? const [];
            if (schedules.isEmpty) {
              return HighlightCard(
                title: l10n.scheduleEmptyTitle,
                subtitle: l10n.scheduleEmptySubtitle,
                icon: Icons.event_busy_outlined,
              );
            }
            final grouped = <String, List<EmployeeReleasedScheduleItem>>{};
            for (final item in schedules) {
              final key = '${item.scheduleDate.year}-${item.scheduleDate.month.toString().padLeft(2, '0')}';
              grouped.putIfAbsent(key, () => []).add(item);
            }
            return Column(
              children: grouped.entries.map((entry) {
                final monthLabel = _monthLabel(entry.value.first.scheduleDate);
                return Card(
                  margin: const EdgeInsets.only(bottom: 14),
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(monthLabel, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                        const SizedBox(height: 12),
                        ...entry.value.map((item) => ListTile(
                              contentPadding: EdgeInsets.zero,
                              title: Text('${_timeLabel(item.workStart)}-${_timeLabel(item.workEnd)} · ${item.shiftLabel}'),
                              subtitle: Text(item.locationLabel ?? '-'),
                              trailing: Chip(label: Text(_statusLabel(item))),
                              onTap: () => _showShiftDetail(item),
                            )),
                      ],
                    ),
                  ),
                );
              }).toList(),
            );
          },
        ),
        Card(
          margin: const EdgeInsets.only(top: 4),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.eventApplicationTitle, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                Text(l10n.eventApplicationSubtitle),
                const SizedBox(height: 12),
                TextField(
                  controller: _planningRecordController,
                  decoration: InputDecoration(labelText: l10n.eventApplicationPlanningRecordLabel),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _applicationNoteController,
                  maxLines: 2,
                  decoration: InputDecoration(labelText: l10n.eventApplicationNoteLabel),
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _submitApplication,
                  icon: const Icon(Icons.send_rounded),
                  label: Text(l10n.eventApplicationSubmit),
                ),
                const SizedBox(height: 12),
                FutureBuilder<List<EmployeeEventApplicationItem>>(
                  future: _applicationsFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const SizedBox.shrink();
                    }
                    if (snapshot.hasError) {
                      return Text(l10n.mobileLoadErrorSubtitle(snapshot.error));
                    }
                    final items = snapshot.data ?? const [];
                    if (items.isEmpty) {
                      return Text(l10n.eventApplicationEmpty);
                    }
                    return Column(
                      children: items
                          .map(
                            (item) => ListTile(
                              contentPadding: EdgeInsets.zero,
                              title: Text(item.planningRecordId),
                              subtitle: Text(item.note ?? '-'),
                              trailing: Wrap(
                                spacing: 8,
                                crossAxisAlignment: WrapCrossAlignment.center,
                                children: [
                                  Chip(label: Text(item.status)),
                                  if (item.status == 'pending')
                                    TextButton(
                                      onPressed: () => _cancelApplication(item),
                                      child: Text(l10n.eventApplicationCancel),
                                    ),
                                ],
                              ),
                            ),
                          )
                          .toList(),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Future<List<EmployeeReleasedScheduleItem>> _loadSchedules() {
    return widget.controller.withAccessToken(widget.backend.fetchReleasedSchedules);
  }

  Future<List<EmployeeEventApplicationItem>> _loadApplications() {
    return widget.controller.withAccessToken(widget.backend.fetchEventApplications);
  }

  void _refresh() {
    setState(() {
      _schedulesFuture = _loadSchedules();
      _applicationsFuture = _loadApplications();
    });
  }

  String _monthLabel(DateTime value) => '${value.month.toString().padLeft(2, '0')}.${value.year}';
  String _timeLabel(DateTime value) => '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';
  String _statusLabel(EmployeeReleasedScheduleItem item) => item.confirmationStatus == 'confirmed' ? context.l10n.mobileStatusConfirmed : context.l10n.mobileStatusAssigned;

  Future<void> _showShiftDetail(EmployeeReleasedScheduleItem item) async {
    final l10n = context.l10n;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
          child: SafeArea(
            child: ListView(
              shrinkWrap: true,
              children: [
                Text(item.shiftLabel, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                Text('${_timeLabel(item.workStart)}-${_timeLabel(item.workEnd)}'),
                const SizedBox(height: 8),
                Text(item.locationLabel ?? '-'),
                if (item.meetingPoint != null) ...[
                  const SizedBox(height: 4),
                  Text('${l10n.scheduleMeetingPoint}: ${item.meetingPoint}'),
                ],
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    FilledButton.icon(
                      onPressed: () => _copyMapUri(item),
                      icon: const Icon(Icons.map_outlined),
                      label: Text(l10n.scheduleMapAction),
                    ),
                    FilledButton.tonalIcon(
                      onPressed: () => _respond(item, 'confirm'),
                      icon: const Icon(Icons.check_circle_outline_rounded),
                      label: Text(l10n.scheduleConfirmAction),
                    ),
                    FilledButton.tonalIcon(
                      onPressed: () => _respond(item, 'decline'),
                      icon: const Icon(Icons.cancel_outlined),
                      label: Text(l10n.scheduleDeclineAction),
                    ),
                    FilledButton.tonalIcon(
                      onPressed: () => _exportCalendar(item),
                      icon: const Icon(Icons.event_available_rounded),
                      label: Text(l10n.scheduleCalendarExportAction),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(l10n.scheduleDocumentsTitle, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                if (item.documents.isEmpty)
                  Text(l10n.scheduleDocumentsEmpty)
                else
                  ...item.documents.map(
                    (document) => ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(document.title),
                      subtitle: Text(document.fileName ?? '-'),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _copyMapUri(EmployeeReleasedScheduleItem item) async {
    final l10n = context.l10n;
    final location = Uri.encodeComponent(item.locationLabel ?? item.meetingPoint ?? '');
    final uri = 'https://www.google.com/maps/search/?api=1&query=$location';
    await Clipboard.setData(ClipboardData(text: uri));
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.scheduleMapCopied)));
  }

  Future<void> _respond(EmployeeReleasedScheduleItem item, String responseCode) async {
    final l10n = context.l10n;
    await widget.controller.withAccessToken(
      (token) => widget.backend.respondToAssignment(
        token,
        assignmentId: item.id,
        responseCode: responseCode,
        versionNo: null,
      ),
    );
    if (!mounted) {
      return;
    }
    Navigator.of(context).pop();
    _refresh();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(responseCode == 'confirm' ? l10n.scheduleConfirmDone : l10n.scheduleDeclineDone)),
    );
  }

  Future<void> _submitApplication() async {
    final planningRecordId = _planningRecordController.text.trim();
    if (planningRecordId.isEmpty) {
      return;
    }
    await widget.controller.withAccessToken(
      (token) => widget.backend.createEventApplication(
        token,
        planningRecordId: planningRecordId,
        note: _applicationNoteController.text.trim().isEmpty ? null : _applicationNoteController.text.trim(),
      ),
    );
    _planningRecordController.clear();
    _applicationNoteController.clear();
    if (!mounted) {
      return;
    }
    _refresh();
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(context.l10n.eventApplicationCreated)));
  }

  Future<void> _cancelApplication(EmployeeEventApplicationItem item) async {
    await widget.controller.withAccessToken(
      (token) => widget.backend.cancelEventApplication(
        token,
        applicationId: item.id,
        versionNo: item.versionNo,
      ),
    );
    if (!mounted) {
      return;
    }
    _refresh();
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(context.l10n.eventApplicationCancelled)));
  }

  Future<void> _exportCalendar(EmployeeReleasedScheduleItem item) async {
    final start = '${item.workStart.toUtc().toIso8601String().replaceAll('-', '').replaceAll(':', '').split('.').first}Z';
    final end = '${item.workEnd.toUtc().toIso8601String().replaceAll('-', '').replaceAll(':', '').split('.').first}Z';
    final ics = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//SicherPlan//Employee Mobile//DE',
      'BEGIN:VEVENT',
      'UID:${item.id}',
      'DTSTART:$start',
      'DTEND:$end',
      'SUMMARY:${item.shiftLabel}',
      'LOCATION:${item.locationLabel ?? ''}',
      'DESCRIPTION:${item.meetingPoint ?? ''}',
      'END:VEVENT',
      'END:VCALENDAR',
    ].join('\r\n');
    final file = File('${Directory.systemTemp.path}/shift-${item.id}.ics');
    await file.writeAsString(ics, flush: true);
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(context.l10n.scheduleCalendarExported(file.path))));
  }
}
