# Changelog

## [1.7.0](https://github.com/BlueBrain/dir-content-diff/compare/1.6.0..1.7.0)

> 5 February 2024

### New Features

- Add 'replace_pattern' entry for DictComparator and several related save capabilities (Adrien Berchet - [#53](https://github.com/BlueBrain/dir-content-diff/pull/53))
- Add 'patterns' entry in specific_args (Adrien Berchet - [#52](https://github.com/BlueBrain/dir-content-diff/pull/52))

## [1.6.0](https://github.com/BlueBrain/dir-content-diff/compare/1.5.0..1.6.0)

> 29 January 2024

### New Features

- The specific_args can support a 'comparator' entry (Adrien Berchet - [#48](https://github.com/BlueBrain/dir-content-diff/pull/48))

### CI Improvements

- (deps) Bump mikepenz/action-junit-report from 3 to 4 (dependabot[bot] - [#39](https://github.com/BlueBrain/dir-content-diff/pull/39))
- (deps) Bump actions/checkout from 3 to 4 (dependabot[bot] - [#38](https://github.com/BlueBrain/dir-content-diff/pull/38))
- Improve Dependabot config (Adrien Berchet - [#40](https://github.com/BlueBrain/dir-content-diff/pull/40))

## [1.5.0](https://github.com/BlueBrain/dir-content-diff/compare/1.4.0..1.5.0)

> 11 May 2023

### New Features

- Add exception type before arguments (Adrien Berchet - [#36](https://github.com/BlueBrain/dir-content-diff/pull/36))

### Fixes

- Cast exception args to str before joining them (Adrien Berchet - [#35](https://github.com/BlueBrain/dir-content-diff/pull/35))

### Changes to Test Assests

- Fix for Pandas&gt;=2 (Adrien Berchet - [#33](https://github.com/BlueBrain/dir-content-diff/pull/33))

### CI Improvements

- Add template for issues and pull requests (Adrien Berchet - [#34](https://github.com/BlueBrain/dir-content-diff/pull/34))

## [1.4.0](https://github.com/BlueBrain/dir-content-diff/compare/1.3.0..1.4.0)

> 13 March 2023

### Build

- Bump dicttoxml (Adrien Berchet - [#26](https://github.com/BlueBrain/dir-content-diff/pull/26))

### New Features

- Add comparator for INI files (Adrien Berchet - [#28](https://github.com/BlueBrain/dir-content-diff/pull/28))

### Fixes

- Fix supported types reported in the exception when the type is unknown (Adrien Berchet - [#25](https://github.com/BlueBrain/dir-content-diff/pull/25))

### CI Improvements

- Setup min_versions job (Adrien Berchet - [#27](https://github.com/BlueBrain/dir-content-diff/pull/27))

## [1.3.0](https://github.com/BlueBrain/dir-content-diff/compare/1.2.0..1.3.0)

> 19 December 2022

### Chores And Housekeeping

- Use pdf_similar from diff_pdf_visually instead of pdfdiff (Adrien Berchet - [#22](https://github.com/BlueBrain/dir-content-diff/pull/22))

### CI Improvements

- Apply Copier template (Adrien Berchet - [#23](https://github.com/BlueBrain/dir-content-diff/pull/23))

## [1.2.0](https://github.com/BlueBrain/dir-content-diff/compare/1.1.0..1.2.0)

> 30 August 2022

### Refactoring and Updates

- Apply Copier template (Adrien Berchet - [#19](https://github.com/BlueBrain/dir-content-diff/pull/19))

### CI Improvements

- Use commitlint to check PR titles (Adrien Berchet - [#18](https://github.com/BlueBrain/dir-content-diff/pull/18))
- Setup pre-commit and format the files accordingly (Adrien Berchet - [#17](https://github.com/BlueBrain/dir-content-diff/pull/17))

### General Changes

- Updating copyright year (bbpgithubaudit - [#15](https://github.com/BlueBrain/dir-content-diff/pull/15))
- Bump black (Adrien Berchet - [#16](https://github.com/BlueBrain/dir-content-diff/pull/16))
- Add codespell in lint (Adrien Berchet - [#14](https://github.com/BlueBrain/dir-content-diff/pull/14))
- Add missing types in doc of DictComparator.diff (Adrien Berchet - [#13](https://github.com/BlueBrain/dir-content-diff/pull/13))

<!-- auto-changelog-above -->

## [1.1.0](https://github.com/BlueBrain/dir-content-diff/compare/1.0.1..1.1.0)

> 21 January 2022

- Require changes for CodeCov (Adrien Berchet - [#11](https://github.com/BlueBrain/dir-content-diff/pull/11))
- Add pandas HDF capability (Alexis Arnaudon - [#10](https://github.com/BlueBrain/dir-content-diff/pull/10))
- Fix tests for rst2pdf&gt;0.99 (Adrien Berchet - [#9](https://github.com/BlueBrain/dir-content-diff/pull/9))
- Setup Codecov (Adrien Berchet - [#8](https://github.com/BlueBrain/dir-content-diff/pull/8))

## [1.0.1](https://github.com/BlueBrain/dir-content-diff/compare/1.0.0..1.0.1)

> 16 December 2021

- Improve documentation (Adrien Berchet - [#6](https://github.com/BlueBrain/dir-content-diff/pull/6))

## [1.0.0](https://github.com/BlueBrain/dir-content-diff/compare/0.2.0..1.0.0)

> 15 December 2021

- Fix URL (Adrien Berchet - [#3](https://github.com/BlueBrain/dir-content-diff/pull/3))
- README.md spelling update (alex4200 - [#2](https://github.com/BlueBrain/dir-content-diff/pull/2))
- Change license and open the sources (Adrien Berchet - [#1](https://github.com/BlueBrain/dir-content-diff/pull/1))

## [0.2.0](https://github.com/BlueBrain/dir-content-diff/compare/0.1.0..0.2.0)

> 15 September 2021

- Add generic export feature and pytest plugin (Adrien Berchet - [23a9298](https://github.com/BlueBrain/dir-content-diff/commit/23a929835d826c2f8fc6ff4c645fea8fffe7c3cc))

## [0.1.0](https://github.com/BlueBrain/dir-content-diff/compare/0.0.5..0.1.0)

> 11 September 2021

- Add an XML comparator (Adrien Berchet - [5dbbec3](https://github.com/BlueBrain/dir-content-diff/commit/5dbbec3aa73245b24652885fcfd0bbde4adf02c2))

## [0.0.5](https://github.com/BlueBrain/dir-content-diff/compare/0.0.4..0.0.5)

> 7 September 2021

- Add a BaseComparator class from which the comparators should inherit (Adrien Berchet - [5253c3b](https://github.com/BlueBrain/dir-content-diff/commit/5253c3b88f9d3f75adf224558cd2a9046fe7db55))
- Setup auto-changelog (Adrien Berchet - [3eb9e93](https://github.com/BlueBrain/dir-content-diff/commit/3eb9e93054af952f8810986a5d3568f324537c71))
- Delete CHANGELOG.rst (Adrien Berchet - [8dcc533](https://github.com/BlueBrain/dir-content-diff/commit/8dcc5336bc66df0d51315789ca5a6395576172a4))

## [0.0.4](https://github.com/BlueBrain/dir-content-diff/compare/0.0.3..0.0.4)

> 28 July 2021

- Move inner part of compare_trees() to compare_files() (Adrien Berchet - [3f45f4e](https://github.com/BlueBrain/dir-content-diff/commit/3f45f4e964fc09a9ce16bb7bd22b5df00aa7f7fd))
- Use pytest template to improve reports and coverage (Adrien Berchet - [d639412](https://github.com/BlueBrain/dir-content-diff/commit/d639412a719ad3708bbe890429c7c5dd9b420a83))
- Migrate the CI from Jenkins to GitLab (Adrien Berchet - [5e7058f](https://github.com/BlueBrain/dir-content-diff/commit/5e7058ffcd8781fab97aa8917abc72cabd886cfc))

## [0.0.3](https://github.com/BlueBrain/dir-content-diff/compare/0.0.2..0.0.3)

> 13 April 2021

- Add function to save modified CSV files (Adrien Berchet - [b1b139a](https://github.com/BlueBrain/dir-content-diff/commit/b1b139a79f1aaaf4ff8fe65c3ded8a227958b257))

## [0.0.2](https://github.com/BlueBrain/dir-content-diff/compare/0.0.1..0.0.2)

> 26 February 2021

- Add regex flags in pandas replace (Adrien Berchet - [66c2b83](https://github.com/BlueBrain/dir-content-diff/commit/66c2b83393b7b31b9a047952a0169cbfbd220932))

## 0.0.1

> 26 February 2021

- Initial commit (Adrien Berchet - [c79ae4e](https://github.com/BlueBrain/dir-content-diff/commit/c79ae4ed6a6262da5a7f09d5b691168f73bc0bae))
- Clean doc (Adrien Berchet - [d7c65ad](https://github.com/BlueBrain/dir-content-diff/commit/d7c65ad4b266939864704082cda822eba17cf2ec))
