import * as SFP from 'studio/util/stringifyForPython';

test('writeString', () => {
  expect(SFP.writeString("Hello '' world '"))
    .toBe(`(r'''Hello '''+"'"+r''''''+"'"+r''' world '''+"'"+r'''''')`)
});
