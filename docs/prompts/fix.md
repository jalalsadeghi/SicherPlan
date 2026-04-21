Perform a safety review after the Overview nav fix.

Checklist:
1. The left nav is sticky and visible during scroll.
2. The sticky behavior works inside the actual app scroll container, not only theoretically.
3. Scroll spy updates activeOverviewSection during manual scroll.
4. Click navigation still works.
5. There is no boxed/card wrapper around nav links.
6. Links are not styled as pills.
7. Real icons are used.
8. Icons are accessible/decorative correctly.
9. Section cards still have clear visual separation.
10. All Overview section actions remain functional.
11. Dashboard tab remains unchanged.
12. Create employee mode remains unchanged.
13. Private sections still respect canReadPrivate.
14. No global styles accidentally affect Customer nav or other modules.

If any item fails, fix it before finalizing.

Final response must explicitly state:
- how sticky nav was implemented
- how active section detection works
- which icon component/library is used
- what tests were run.