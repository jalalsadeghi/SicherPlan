enum MobileRole {
  employee(code: 'employee'),
  fieldSupervisor(code: 'field_supervisor'),
  restrictedField(code: 'restricted_field');

  const MobileRole({required this.code});

  final String code;
}
