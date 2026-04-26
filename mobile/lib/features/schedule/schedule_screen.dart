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
    this.nowProvider = DateTime.now,
    super.key,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;
  final DateTime Function() nowProvider;

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
    return Scaffold(
      body: ShellScaffold(
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
              final schedules = snapshot.data ?? const [];
              final hasError = snapshot.hasError;
              if (schedules.isEmpty) {
                final weekStarts = _buildCalendarWeekStarts(schedules);
                return Column(
                  children: [
                    HighlightCard(
                      title: hasError
                          ? l10n.scheduleErrorTitle
                          : l10n.scheduleEmptyTitle,
                      subtitle: hasError
                          ? l10n.mobileLoadErrorSubtitle(snapshot.error)
                          : l10n.scheduleEmptySubtitle,
                      icon: hasError
                          ? Icons.error_outline_rounded
                          : Icons.event_busy_outlined,
                    ),
                    const SizedBox(height: 14),
                    Card(
                      margin: const EdgeInsets.only(bottom: 14),
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: _ScheduleWeekList(
                          key: const ValueKey('schedule-week-list'),
                          weekStarts: weekStarts,
                          schedulesByDay:
                              const <
                                DateTime,
                                List<EmployeeReleasedScheduleItem>
                              >{},
                          timeLabel: _timeLabel,
                          statusLabel: _statusLabel,
                          isToday: _isToday,
                          onShiftSelected: _showShiftDetail,
                        ),
                      ),
                    ),
                  ],
                );
              }
              final sortedSchedules = [...schedules]
                ..sort(
                  (left, right) => left.workStart.compareTo(right.workStart),
                );
              final schedulesByDay = _groupSchedulesByDay(sortedSchedules);
              final weekStarts = _buildCalendarWeekStarts(sortedSchedules);
              return Column(
                children: [
                  if (hasError)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 14),
                      child: HighlightCard(
                        title: l10n.scheduleErrorTitle,
                        subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                        icon: Icons.error_outline_rounded,
                      ),
                    ),
                  Card(
                    margin: const EdgeInsets.only(bottom: 14),
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: _ScheduleWeekList(
                        key: const ValueKey('schedule-week-list'),
                        weekStarts: weekStarts,
                        schedulesByDay: schedulesByDay,
                        timeLabel: _timeLabel,
                        statusLabel: _statusLabel,
                        isToday: _isToday,
                        onShiftSelected: _showShiftDetail,
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
          Card(
            key: const ValueKey('schedule-event-application-card'),
            margin: const EdgeInsets.only(top: 4),
            child: Theme(
              data: Theme.of(
                context,
              ).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                key: const ValueKey('schedule-event-application-tile'),
                tilePadding: const EdgeInsets.symmetric(
                  horizontal: 18,
                  vertical: 4,
                ),
                childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
                initiallyExpanded: false,
                title: Text(
                  l10n.eventApplicationTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                subtitle: Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(l10n.eventApplicationSubtitle),
                ),
                children: [
                  TextField(
                    key: const ValueKey(
                      'event-application-planning-record-field',
                    ),
                    controller: _planningRecordController,
                    decoration: InputDecoration(
                      labelText: l10n.eventApplicationPlanningRecordLabel,
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    key: const ValueKey('event-application-note-field'),
                    controller: _applicationNoteController,
                    maxLines: 2,
                    decoration: InputDecoration(
                      labelText: l10n.eventApplicationNoteLabel,
                    ),
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
                        return Text(
                          l10n.mobileLoadErrorSubtitle(snapshot.error),
                        );
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
                                        onPressed: () =>
                                            _cancelApplication(item),
                                        child: Text(
                                          l10n.eventApplicationCancel,
                                        ),
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
      ),
    );
  }

  Future<List<EmployeeReleasedScheduleItem>> _loadSchedules() {
    return widget.controller.withAccessToken(
      widget.backend.fetchReleasedSchedules,
    );
  }

  Future<List<EmployeeEventApplicationItem>> _loadApplications() {
    return widget.controller.withAccessToken(
      widget.backend.fetchEventApplications,
    );
  }

  void _refresh() {
    setState(() {
      _schedulesFuture = _loadSchedules();
      _applicationsFuture = _loadApplications();
    });
  }

  String _timeLabel(DateTime value) =>
      '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';

  String _statusLabel(String code) => switch (code) {
    'confirmed' => context.l10n.mobileStatusConfirmed,
    'declined' => context.l10n.mobileStatusDeclined,
    'assigned' => context.l10n.mobileStatusAssigned,
    _ => code,
  };

  Map<DateTime, List<EmployeeReleasedScheduleItem>> _groupSchedulesByDay(
    List<EmployeeReleasedScheduleItem> schedules,
  ) {
    final grouped = <DateTime, List<EmployeeReleasedScheduleItem>>{};
    for (final item in schedules) {
      final day = _dateOnly(item.scheduleDate);
      grouped
          .putIfAbsent(day, () => <EmployeeReleasedScheduleItem>[])
          .add(item);
    }
    for (final items in grouped.values) {
      items.sort((left, right) => left.workStart.compareTo(right.workStart));
    }
    return grouped;
  }

  List<DateTime> _buildCalendarWeekStarts(
    List<EmployeeReleasedScheduleItem> schedules,
  ) {
    final anchorWeek = _weekStart(_dateOnly(widget.nowProvider()));
    final defaultStart = anchorWeek.subtract(const Duration(days: 28));
    final defaultEnd = anchorWeek.add(const Duration(days: 84));
    DateTime firstWeek = defaultStart;
    DateTime lastWeek = defaultEnd;
    if (schedules.isNotEmpty) {
      final scheduleFirstWeek = _weekStart(
        _dateOnly(schedules.first.scheduleDate),
      ).subtract(const Duration(days: 28));
      final scheduleLastWeek = _weekStart(
        _dateOnly(schedules.last.scheduleDate),
      ).add(const Duration(days: 84));
      if (scheduleFirstWeek.isBefore(firstWeek)) {
        firstWeek = scheduleFirstWeek;
      }
      if (scheduleLastWeek.isAfter(lastWeek)) {
        lastWeek = scheduleLastWeek;
      }
    }
    final weekStarts = <DateTime>[];
    for (
      var cursor = firstWeek;
      !cursor.isAfter(lastWeek);
      cursor = cursor.add(const Duration(days: 7))
    ) {
      weekStarts.add(cursor);
    }
    return weekStarts;
  }

  DateTime _dateOnly(DateTime value) =>
      DateTime(value.year, value.month, value.day);

  DateTime _weekStart(DateTime value) => _dateOnly(
    value,
  ).subtract(Duration(days: value.weekday - DateTime.monday));

  bool _isToday(DateTime value) {
    final now = DateTime.now();
    return value.year == now.year &&
        value.month == now.month &&
        value.day == now.day;
  }

  Future<void> _showShiftDetail(EmployeeReleasedScheduleItem item) async {
    final l10n = context.l10n;
    final localizations = MaterialLocalizations.of(context);
    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return Dialog(
          key: ValueKey('schedule-shift-dialog-${item.id}'),
          insetPadding: const EdgeInsets.symmetric(
            horizontal: 20,
            vertical: 24,
          ),
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: 560,
              maxHeight: MediaQuery.of(dialogContext).size.height * 0.82,
            ),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              l10n.scheduleShiftDetailsTitle,
                              style: Theme.of(dialogContext)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              item.shiftLabel,
                              style: Theme.of(dialogContext)
                                  .textTheme
                                  .headlineSmall
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.of(dialogContext).pop(),
                        icon: const Icon(Icons.close_rounded),
                        tooltip: l10n.scheduleCloseAction,
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: ListView(
                      shrinkWrap: true,
                      children: [
                        _ShiftDetailRow(
                          label: l10n.scheduleDateLabel,
                          value: localizations.formatFullDate(
                            item.scheduleDate,
                          ),
                        ),
                        _ShiftDetailRow(
                          label: l10n.scheduleTimeLabel,
                          value:
                              '${_timeLabel(item.workStart)}-${_timeLabel(item.workEnd)}',
                        ),
                        _ShiftDetailRow(
                          label: l10n.scheduleLocationLabel,
                          value: item.locationLabel ?? '-',
                        ),
                        _ShiftDetailRow(
                          label: l10n.scheduleMeetingPoint,
                          value: item.meetingPoint ?? '-',
                        ),
                        _ShiftDetailRow(
                          label: l10n.scheduleAssignmentStatusLabel,
                          value: _statusLabel(item.assignmentStatus),
                        ),
                        _ShiftDetailRow(
                          label: l10n.scheduleConfirmationStatusLabel,
                          value: _statusLabel(item.confirmationStatus),
                        ),
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
                              icon: const Icon(
                                Icons.check_circle_outline_rounded,
                              ),
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
                        Text(
                          l10n.scheduleDocumentsTitle,
                          style: Theme.of(dialogContext).textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
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
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: () => Navigator.of(dialogContext).pop(),
                      child: Text(l10n.scheduleCloseAction),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Future<void> _copyMapUri(EmployeeReleasedScheduleItem item) async {
    final l10n = context.l10n;
    final location = Uri.encodeComponent(
      item.locationLabel ?? item.meetingPoint ?? '',
    );
    final uri = 'https://www.google.com/maps/search/?api=1&query=$location';
    await Clipboard.setData(ClipboardData(text: uri));
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(l10n.scheduleMapCopied)));
  }

  Future<void> _respond(
    EmployeeReleasedScheduleItem item,
    String responseCode,
  ) async {
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
      SnackBar(
        content: Text(
          responseCode == 'confirm'
              ? l10n.scheduleConfirmDone
              : l10n.scheduleDeclineDone,
        ),
      ),
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
        note: _applicationNoteController.text.trim().isEmpty
            ? null
            : _applicationNoteController.text.trim(),
      ),
    );
    _planningRecordController.clear();
    _applicationNoteController.clear();
    if (!mounted) {
      return;
    }
    _refresh();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(context.l10n.eventApplicationCreated)),
    );
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
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(context.l10n.eventApplicationCancelled)),
    );
  }

  Future<void> _exportCalendar(EmployeeReleasedScheduleItem item) async {
    final start =
        '${item.workStart.toUtc().toIso8601String().replaceAll('-', '').replaceAll(':', '').split('.').first}Z';
    final end =
        '${item.workEnd.toUtc().toIso8601String().replaceAll('-', '').replaceAll(':', '').split('.').first}Z';
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
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(context.l10n.scheduleCalendarExported(file.path))),
    );
  }
}

class _ScheduleWeekList extends StatelessWidget {
  const _ScheduleWeekList({
    required this.weekStarts,
    required this.schedulesByDay,
    required this.timeLabel,
    required this.statusLabel,
    required this.isToday,
    required this.onShiftSelected,
    super.key,
  });

  final List<DateTime> weekStarts;
  final Map<DateTime, List<EmployeeReleasedScheduleItem>> schedulesByDay;
  final String Function(DateTime value) timeLabel;
  final String Function(String code) statusLabel;
  final bool Function(DateTime day) isToday;
  final Future<void> Function(EmployeeReleasedScheduleItem item)
  onShiftSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (var index = 0; index < weekStarts.length; index++) ...[
          _ScheduleWeekSection(
            weekStart: weekStarts[index],
            schedulesByDay: schedulesByDay,
            timeLabel: timeLabel,
            statusLabel: statusLabel,
            isToday: isToday,
            onShiftSelected: onShiftSelected,
          ),
          if (index < weekStarts.length - 1) const SizedBox(height: 16),
        ],
      ],
    );
  }
}

class _ScheduleWeekSection extends StatelessWidget {
  const _ScheduleWeekSection({
    required this.weekStart,
    required this.schedulesByDay,
    required this.timeLabel,
    required this.statusLabel,
    required this.isToday,
    required this.onShiftSelected,
  });

  final DateTime weekStart;
  final Map<DateTime, List<EmployeeReleasedScheduleItem>> schedulesByDay;
  final String Function(DateTime value) timeLabel;
  final String Function(String code) statusLabel;
  final bool Function(DateTime day) isToday;
  final Future<void> Function(EmployeeReleasedScheduleItem item)
  onShiftSelected;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final localizations = MaterialLocalizations.of(context);
    final weekEnd = weekStart.add(const Duration(days: 6));

    return Container(
      key: ValueKey('schedule-week-section-${_isoDate(weekStart)}'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l10n.scheduleWeekLabel(
              localizations.formatShortMonthDay(weekStart),
              localizations.formatShortMonthDay(weekEnd),
            ),
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 12),
          for (var offset = 0; offset < 7; offset++) ...[
            _ScheduleDayGroup(
              day: weekStart.add(Duration(days: offset)),
              items:
                  schedulesByDay[weekStart.add(Duration(days: offset))] ??
                  const <EmployeeReleasedScheduleItem>[],
              timeLabel: timeLabel,
              statusLabel: statusLabel,
              isToday: isToday(weekStart.add(Duration(days: offset))),
              onShiftSelected: onShiftSelected,
            ),
            if (offset < 6) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _ScheduleDayGroup extends StatelessWidget {
  const _ScheduleDayGroup({
    required this.day,
    required this.items,
    required this.timeLabel,
    required this.statusLabel,
    required this.isToday,
    required this.onShiftSelected,
  });

  final DateTime day;
  final List<EmployeeReleasedScheduleItem> items;
  final String Function(DateTime value) timeLabel;
  final String Function(String code) statusLabel;
  final bool isToday;
  final Future<void> Function(EmployeeReleasedScheduleItem item)
  onShiftSelected;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final colors = Theme.of(context).colorScheme;
    final hasShifts = items.isNotEmpty;

    return Container(
      key: ValueKey('schedule-day-${_isoDate(day)}'),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: hasShifts
            ? colors.primary.withValues(alpha: 0.10)
            : colors.surfaceContainerHighest.withValues(alpha: 0.28),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: hasShifts
              ? colors.primary.withValues(alpha: 0.38)
              : colors.outlineVariant,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  MaterialLocalizations.of(context).formatFullDate(day),
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: hasShifts
                        ? colors.onSurface
                        : colors.onSurface.withValues(alpha: 0.7),
                  ),
                ),
              ),
              if (isToday)
                Chip(
                  label: Text(l10n.scheduleTodayLabel),
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
          const SizedBox(height: 8),
          if (!hasShifts)
            Text(
              l10n.scheduleNoShift,
              key: ValueKey('schedule-day-empty-${_isoDate(day)}'),
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: colors.onSurface.withValues(alpha: 0.68),
              ),
            )
          else
            Column(
              children: [
                for (var index = 0; index < items.length; index++) ...[
                  _ScheduleShiftCard(
                    item: items[index],
                    timeLabel: timeLabel,
                    statusLabel: statusLabel,
                    onTap: () => onShiftSelected(items[index]),
                  ),
                  if (index < items.length - 1) const SizedBox(height: 8),
                ],
              ],
            ),
        ],
      ),
    );
  }
}

class _ScheduleShiftCard extends StatelessWidget {
  const _ScheduleShiftCard({
    required this.item,
    required this.timeLabel,
    required this.statusLabel,
    required this.onTap,
  });

  final EmployeeReleasedScheduleItem item;
  final String Function(DateTime value) timeLabel;
  final String Function(String code) statusLabel;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return InkWell(
      key: ValueKey('schedule-shift-${item.id}'),
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Ink(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: colors.outlineVariant),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 5,
              height: 48,
              decoration: BoxDecoration(
                color: colors.primary,
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${timeLabel(item.workStart)}-${timeLabel(item.workEnd)}',
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    item.shiftLabel,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    item.locationLabel ?? '-',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Chip(
              label: Text(statusLabel(item.confirmationStatus)),
              visualDensity: VisualDensity.compact,
            ),
          ],
        ),
      ),
    );
  }
}

class _ShiftDetailRow extends StatelessWidget {
  const _ShiftDetailRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: Theme.of(
              context,
            ).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 2),
          Text(value),
        ],
      ),
    );
  }
}

String _isoDate(DateTime value) =>
    '${value.year}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
