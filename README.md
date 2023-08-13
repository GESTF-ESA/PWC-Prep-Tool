# PWC-Prep-Tool

PWC-Prep-Tool is a Windows application written in Python that generates [Pesticide in Water Calculator (PWC)](https://www.epa.gov/pesticide-science-and-assessing-pesticide-risks/models-pesticide-risk-assessment#PWC) batchfiles.  Manual parameterization of PWC model runs is time-prohibitive and prone to human error due to label restrictions unique to each use site and region and the complexity of the batch file​.  Ensuring conservatism (_e.g._, simulation of applications during wettest months of the year) greatly complicates date assignment logic.  ​PWC-Prep-Tool automates PWC batch file preparation and generates label-compliant application dates and rates. It also allows the user to create runs with landscape scale refinements such as alternate distances, drift factors and transport mechanisms.

PWC-Prep-Tool was created by Pyxis Regulatory Consulting, Inc. and [Applied Analysis Solutions LLC](http://appliedanalysis.solutions/) for the Generic Endangered Species Task Force (GESTF), and is maintained by the GESTF.

## [](https://github.com/gestf-esa/pwc-tool/README.md#requirements)Requirements

Before you begin, please ensure you meet the following requirements:

-   You are running Windows 7 or later (this software has been tested on Windows 10 and 11)
-   You have downloaded the [latest release](https://github.com/GESTF-ESA/PWC-Prep-Tool/releases) and installed it on your computer
-   You have read the [PWC-Prep-Tool User's Guide](https://github.com/GESTF-ESA/PWC-Prep-Tool/docs/PWC-Prep-ToolUsersGuide.pdf) in the `/docs` folder

## [](https://github.com/gestf-esa/pwc-prep-tool/README.md#contributing-to-pwc-prep-tool)Contributing to PWC-Prep-Tool

Contributions are welcome.  To contribute to PWC-Prep-Tool, follow these steps:
1.  Fork this repository
2.  Clone the forked repository to your local development system
3.  Code your changes and commit them
4.  Push your changes to your forked repository on GitHub
5.  _Prior to making a pull request_, make sure you are current with the source GESTF-ESA/PWC-Prep-Tool repository (by [merging or rebasing](https://www.atlassian.com/git/tutorials/merging-vs-rebasing#the-golden-rule-of-rebasing) if necessary and resolving any conflicts)
6.  Create a pull request

For more detailed information, see the GitHub guide [Forking Projects](https://guides.github.com/activities/forking/).

## [](https://github.com/gestf-esa/pwc-prep-tool/README.md#contact)Contact

Suggestions, bug reports and other code / functionality related requests may be made by [submitting an issue](https://github.com/GESTF-ESA/PWC-Prep-Tool/issues).  For questions and additional information, please email [tools@gestf.org](mailto:tools@gestf.org).

## [](https://github.com/gestf-esa/pwc-prep-tool/README.md#license)License

Copyright &copy; 2022-2023 Generic Endangered Species Task Force (GESTF)

This project is licensed under the [GNU General Public License v3.0](https://github.com/GESTF-ESA/PWC-Prep-Tool/blob/main/LICENSE).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

A copy of the license is available in the repository's [LICENSE](https://github.com/GESTF-ESA/PWC-Tool/LICENSE) file.
