import 'package:flutter/material.dart';

import '../../api/mobile_backend.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class TimeCaptureScreen extends StatefulWidget {
  const TimeCaptureScreen({
    required this.controller,
    required this.backend,
    super.key,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;

  @override
  State<TimeCaptureScreen> createState() => _TimeCaptureScreenState();
}

class _TimeCaptureScreenState extends State<TimeCaptureScreen> {
  late Future<List<EmployeeReleasedScheduleItem>> _schedulesFuture;
  late Future<List<TimeCaptureEventItem>> _eventsFuture;

  final _noteController = TextEditingController();
  final _tokenController = TextEditingController();
  final _latitudeController = TextEditingController();
  final _longitudeController = TextEditingController();

  String? _selectedShiftId;
  String _selectedEventCode = 'clock_in';
  String _selectedScanMedium = 'manual';
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _schedulesFuture = _loadSchedules();
    _eventsFuture = _loadEvents();
  }

  @override
  void dispose() {
    _noteController.dispose();
    _tokenController.dispose();
    _latitudeController.dispose();
    _longitudeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ShellScaffold(
      title: l10n.timeTitle,
      subtitle: l10n.timeSubtitle,
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
                title: l10n.timeErrorTitle,
                subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                icon: Icons.error_outline_rounded,
              );
            }
            final schedules = snapshot.data ?? const [];
            if (schedules.isEmpty) {
              return HighlightCard(
                title: l10n.timeEmptyTitle,
                subtitle: l10n.timeEmptySubtitle,
                icon: Icons.timer_off_outlined,
              );
            }
            _selectedShiftId ??= schedules.first.shiftId;
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(l10n.timeCaptureFormTitle, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: 8),
                    Text(l10n.timeCaptureFormSubtitle),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      key: ValueKey('shift-${_selectedShiftId ?? ''}'),
                      initialValue: _selectedShiftId,
                      decoration: InputDecoration(labelText: l10n.timeShiftLabel),
                      items: schedules
                          .map(
                            (item) => DropdownMenuItem<String>(
                              value: item.shiftId,
                              child: Text('${_timeLabel(item.workStart)}-${_timeLabel(item.workEnd)} · ${item.shiftLabel}'),
                            ),
                          )
                          .toList(growable: false),
                      onChanged: (value) => setState(() => _selectedShiftId = value),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      key: ValueKey('event-$_selectedEventCode'),
                      initialValue: _selectedEventCode,
                      decoration: InputDecoration(labelText: l10n.timeEventCodeLabel),
                      items: const [
                        DropdownMenuItem(value: 'clock_in', child: Text('clock_in')),
                        DropdownMenuItem(value: 'clock_out', child: Text('clock_out')),
                        DropdownMenuItem(value: 'break_start', child: Text('break_start')),
                        DropdownMenuItem(value: 'break_end', child: Text('break_end')),
                      ],
                      onChanged: (value) => setState(() => _selectedEventCode = value ?? 'clock_in'),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      key: ValueKey('scan-$_selectedScanMedium'),
                      initialValue: _selectedScanMedium,
                      decoration: InputDecoration(labelText: l10n.timeScanMediumLabel),
                      items: const [
                        DropdownMenuItem(value: 'manual', child: Text('manual')),
                        DropdownMenuItem(value: 'app_badge', child: Text('app_badge')),
                        DropdownMenuItem(value: 'barcode', child: Text('barcode')),
                        DropdownMenuItem(value: 'qr', child: Text('qr')),
                        DropdownMenuItem(value: 'nfc', child: Text('nfc')),
                        DropdownMenuItem(value: 'rfid', child: Text('rfid')),
                      ],
                      onChanged: (value) => setState(() => _selectedScanMedium = value ?? 'manual'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _tokenController,
                      decoration: InputDecoration(
                        labelText: l10n.timeTokenLabel,
                        hintText: l10n.timeTokenHint,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _latitudeController,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                            decoration: InputDecoration(labelText: l10n.timeLatitudeLabel),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextField(
                            controller: _longitudeController,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                            decoration: InputDecoration(labelText: l10n.timeLongitudeLabel),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _noteController,
                      maxLines: 2,
                      decoration: InputDecoration(labelText: l10n.timeNoteLabel),
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: _submitting ? null : _submit,
                      icon: _submitting
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.timer_rounded),
                      label: Text(l10n.timeSubmitAction),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
        FutureBuilder<List<TimeCaptureEventItem>>(
          future: _eventsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const SizedBox.shrink();
            }
            if (snapshot.hasError) {
              return HighlightCard(
                title: l10n.timeHistoryTitle,
                subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                icon: Icons.history_toggle_off_rounded,
              );
            }
            final items = snapshot.data ?? const [];
            if (items.isEmpty) {
              return HighlightCard(
                title: l10n.timeHistoryTitle,
                subtitle: l10n.timeHistoryEmptySubtitle,
                icon: Icons.history_rounded,
              );
            }
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(l10n.timeHistoryTitle, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: 12),
                    ...items.map(
                      (item) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                          item.validationStatusCode == 'accepted'
                              ? Icons.check_circle_outline_rounded
                              : item.validationStatusCode == 'flagged'
                              ? Icons.warning_amber_rounded
                              : Icons.block_outlined,
                        ),
                        title: Text('${item.eventCode} · ${_timeLabel(item.occurredAt)}'),
                        subtitle: Text(
                          item.validationMessageKey == null
                              ? item.sourceChannelCode
                              : '${item.sourceChannelCode} · ${l10n.backendMessage(item.validationMessageKey!)}',
                        ),
                        trailing: Text(item.rawTokenSuffix ?? ''),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ],
    );
  }

  Future<List<EmployeeReleasedScheduleItem>> _loadSchedules() {
    return widget.controller.withAccessToken(widget.backend.fetchReleasedSchedules);
  }

  Future<List<TimeCaptureEventItem>> _loadEvents() {
    return widget.controller.withAccessToken(widget.backend.fetchTimeEvents);
  }

  void _refresh() {
    setState(() {
      _schedulesFuture = _loadSchedules();
      _eventsFuture = _loadEvents();
    });
  }

  String _timeLabel(DateTime value) => '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';

  Future<void> _submit() async {
    if (_selectedShiftId == null) {
      return;
    }
    setState(() {
      _submitting = true;
    });
    try {
      final latitude = double.tryParse(_latitudeController.text.trim());
      final longitude = double.tryParse(_longitudeController.text.trim());
      await widget.controller.withAccessToken(
        (accessToken) => widget.backend.captureOwnTimeEvent(
          accessToken,
          sourceChannelCode: 'mobile',
          payload: TimeCapturePayload(
            shiftId: _selectedShiftId!,
            eventCode: _selectedEventCode,
            occurredAt: DateTime.now().toUtc(),
            latitude: latitude,
            longitude: longitude,
            note: _noteController.text.trim().isEmpty ? null : _noteController.text.trim(),
            rawToken: _tokenController.text.trim().isEmpty ? null : _tokenController.text.trim(),
            scanMediumCode: _selectedScanMedium,
            clientEventId: 'mobile-${DateTime.now().microsecondsSinceEpoch}',
          ),
        ),
      );
      if (!mounted) return;
      _noteController.clear();
      _tokenController.clear();
      _latitudeController.clear();
      _longitudeController.clear();
      _refresh();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(context.l10n.timeSubmitSuccess)),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is MobileApiException ? context.l10n.backendMessage(error.messageKey) : context.l10n.mobileLoadErrorSubtitle(error);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) {
        setState(() {
          _submitting = false;
        });
      }
    }
  }
}
