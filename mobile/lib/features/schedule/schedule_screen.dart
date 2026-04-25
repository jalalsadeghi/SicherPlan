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
  DateTime? _visibleMonth;

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
            final sortedSchedules = [
              ...schedules,
            ]..sort((left, right) => left.workStart.compareTo(right.workStart));
            final minMonth = _monthStart(sortedSchedules.first.scheduleDate);
            final maxMonth = _monthStart(sortedSchedules.last.scheduleDate);
            final visibleMonth = _resolveVisibleMonth(minMonth, maxMonth);
            final schedulesByDay = _groupSchedulesByDay(sortedSchedules);
            return Column(
              children: [
                Card(
                  margin: const EdgeInsets.only(bottom: 14),
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            IconButton(
                              onPressed: visibleMonth.isAfter(minMonth)
                                  ? () => _changeVisibleMonth(-1)
                                  : null,
                              icon: const Icon(Icons.chevron_left_rounded),
                            ),
                            Expanded(
                              child: Text(
                                MaterialLocalizations.of(
                                  context,
                                ).formatMonthYear(visibleMonth),
                                key: const ValueKey(
                                  'schedule-calendar-month-label',
                                ),
                                textAlign: TextAlign.center,
                                style: Theme.of(context).textTheme.titleMedium
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                            ),
                            IconButton(
                              onPressed: visibleMonth.isBefore(maxMonth)
                                  ? () => _changeVisibleMonth(1)
                                  : null,
                              icon: const Icon(Icons.chevron_right_rounded),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        _CalendarMonthView(
                          visibleMonth: visibleMonth,
                          schedulesByDay: schedulesByDay,
                          timeLabel: _timeLabel,
                          statusLabel: _statusLabel,
                          onDaySelected: _showDayDetail,
                        ),
                      ],
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
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
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
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
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
  String _statusLabel(EmployeeReleasedScheduleItem item) =>
      item.confirmationStatus == 'confirmed'
      ? context.l10n.mobileStatusConfirmed
      : context.l10n.mobileStatusAssigned;

  DateTime _resolveVisibleMonth(DateTime minMonth, DateTime maxMonth) {
    final current = _visibleMonth;
    if (current == null ||
        current.isBefore(minMonth) ||
        current.isAfter(maxMonth)) {
      _visibleMonth = minMonth;
    }
    return _visibleMonth!;
  }

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

  DateTime _monthStart(DateTime value) => DateTime(value.year, value.month);
  DateTime _dateOnly(DateTime value) =>
      DateTime(value.year, value.month, value.day);

  void _changeVisibleMonth(int monthDelta) {
    final visibleMonth = _visibleMonth;
    if (visibleMonth == null) {
      return;
    }
    setState(() {
      _visibleMonth = DateTime(
        visibleMonth.year,
        visibleMonth.month + monthDelta,
      );
    });
  }

  Future<void> _showDayDetail(
    DateTime day,
    List<EmployeeReleasedScheduleItem> items,
  ) async {
    final localizations = MaterialLocalizations.of(context);
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
                Text(
                  localizations.formatFullDate(day),
                  key: const ValueKey('schedule-day-sheet-title'),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 12),
                ...items.map(
                  (item) => ListTile(
                    key: ValueKey('schedule-day-shift-${item.id}'),
                    contentPadding: EdgeInsets.zero,
                    title: Text(
                      '${_timeLabel(item.workStart)}-${_timeLabel(item.workEnd)} · ${item.shiftLabel}',
                    ),
                    subtitle: Text(item.locationLabel ?? '-'),
                    trailing: Chip(label: Text(_statusLabel(item))),
                    onTap: () => _showShiftDetail(item),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

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
                Text(
                  item.shiftLabel,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '${_timeLabel(item.workStart)}-${_timeLabel(item.workEnd)}',
                ),
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
                Text(
                  l10n.scheduleDocumentsTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
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

class _CalendarMonthView extends StatelessWidget {
  const _CalendarMonthView({
    required this.visibleMonth,
    required this.schedulesByDay,
    required this.timeLabel,
    required this.statusLabel,
    required this.onDaySelected,
  });

  final DateTime visibleMonth;
  final Map<DateTime, List<EmployeeReleasedScheduleItem>> schedulesByDay;
  final String Function(DateTime value) timeLabel;
  final String Function(EmployeeReleasedScheduleItem item) statusLabel;
  final Future<void> Function(
    DateTime day,
    List<EmployeeReleasedScheduleItem> items,
  )
  onDaySelected;

  @override
  Widget build(BuildContext context) {
    final localizations = MaterialLocalizations.of(context);
    final orderedWeekdays = _orderedWeekdays(localizations);
    final monthDays = _monthGridDays(localizations);

    return Column(
      children: [
        Row(
          children: orderedWeekdays
              .map(
                (weekday) => Expanded(
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        weekday,
                        style: Theme.of(context).textTheme.labelMedium
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                ),
              )
              .toList(growable: false),
        ),
        GridView.builder(
          key: const ValueKey('schedule-calendar-grid'),
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: monthDays.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 7,
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            childAspectRatio: 0.9,
          ),
          itemBuilder: (context, index) {
            final day = monthDays[index];
            if (day == null) {
              return const SizedBox.shrink();
            }
            final items =
                schedulesByDay[day] ?? const <EmployeeReleasedScheduleItem>[];
            final hasShifts = items.isNotEmpty;
            final isCurrentMonth = day.month == visibleMonth.month;
            return _CalendarDayCell(
              day: day,
              items: items,
              hasShifts: hasShifts,
              isCurrentMonth: isCurrentMonth,
              onTap: hasShifts ? () => onDaySelected(day, items) : null,
            );
          },
        ),
      ],
    );
  }

  List<String> _orderedWeekdays(MaterialLocalizations localizations) {
    final weekdays = localizations.narrowWeekdays;
    final firstDay = localizations.firstDayOfWeekIndex;
    return List<String>.generate(
      7,
      (index) => weekdays[(firstDay + index) % 7],
      growable: false,
    );
  }

  List<DateTime?> _monthGridDays(MaterialLocalizations localizations) {
    final firstOfMonth = DateTime(visibleMonth.year, visibleMonth.month, 1);
    final lastOfMonth = DateTime(visibleMonth.year, visibleMonth.month + 1, 0);
    final firstDayOffset =
        (firstOfMonth.weekday % 7 - localizations.firstDayOfWeekIndex + 7) % 7;
    final totalCells = ((firstDayOffset + lastOfMonth.day + 6) ~/ 7) * 7;
    return List<DateTime?>.generate(totalCells, (index) {
      final dayNumber = index - firstDayOffset + 1;
      if (dayNumber < 1 || dayNumber > lastOfMonth.day) {
        return null;
      }
      return DateTime(visibleMonth.year, visibleMonth.month, dayNumber);
    }, growable: false);
  }
}

class _CalendarDayCell extends StatelessWidget {
  const _CalendarDayCell({
    required this.day,
    required this.items,
    required this.hasShifts,
    required this.isCurrentMonth,
    required this.onTap,
  });

  final DateTime day;
  final List<EmployeeReleasedScheduleItem> items;
  final bool hasShifts;
  final bool isCurrentMonth;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final firstShift = items.isEmpty ? null : items.first;
    final shiftSummary = firstShift == null
        ? null
        : '${firstShift.workStart.hour.toString().padLeft(2, '0')}:${firstShift.workStart.minute.toString().padLeft(2, '0')} ${firstShift.shiftLabel}';

    return InkWell(
      key: ValueKey(
        'schedule-calendar-day-${day.year}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}',
      ),
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Ink(
        decoration: BoxDecoration(
          color: hasShifts
              ? colors.primary.withValues(alpha: 0.12)
              : colors.surfaceContainerHighest.withValues(alpha: 0.35),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: hasShifts
                ? colors.primary.withValues(alpha: 0.5)
                : colors.outlineVariant,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${day.day}',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: isCurrentMonth
                      ? colors.onSurface
                      : colors.onSurface.withValues(alpha: 0.45),
                ),
              ),
              const Spacer(),
              if (hasShifts) ...[
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: colors.primary,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    items.length == 1 ? '1' : '${items.length}',
                    key: ValueKey(
                      'schedule-calendar-day-count-${day.year}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}',
                    ),
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: colors.onPrimary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  shiftSummary!,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(
                    context,
                  ).textTheme.labelSmall?.copyWith(fontWeight: FontWeight.w600),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
