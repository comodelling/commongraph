
# Democratic Modelling


## Support ratings
Users are encouraged to voice their level of support for each potential change, responding to the question *"How much do you support this change?"* for each node they select.
Ratings follow a Likert scale from **1** (not at all) to **5** (strongly).
Note that these ratings will are anonymised on the UI, and pseudo-anonymised in the database.

## Causal ratings
Users are also asked, for each edge they select: *"To what extent does C\[ondition\] contribute to O\[utcome\]?"*.
This causal strength is meant to be general, encompassing several causal mechanisms: enabling, causing, influencing, implying.


## Aggregating and debiasing

Ratings are currently aggregated according to their median (e.g., on the [browsing view](../view/browsing.md) or to select a colour on the [flow pane](../view/focus.md#flow-pane))
Further down the line, the overall measure of support will be debiased within every node's scope.
