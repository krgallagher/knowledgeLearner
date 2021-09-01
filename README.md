# kLearner

kLearner (Knowledge Learner) is a new story-based question and answering system that uses the Learning from Answer Sets paradigm of 
Inductive Logic Programming to learn commonsense reasoning knowledge from story-based question and answering in English 
across three discourse mediums: text, written dialogue, and spoken dialogue. 



#Usage 
In order to use this system, the following must be installed: 
* python 3.9.5
* all python libraries in requirements.txt
* ILASP v. 4.1.1 
* Clingo v. 5.5.0
* mpg321 

This system is run on the command line using the file OverallPipeline.py in the module SystemPipeline.
The following command line arguments are required, depending on whether the user wants to use the dataset or dialogue
mode of the system: 
* Dataset -component=dataset \[training file\] \[testing file\]
* Dialogue -component=dialogue -dialogueMethod=\[spoken|written\]

If the user is using the dataset mode, then the following optional command line arguments may be added 
after the required arguments: 
* -s                          use strong supervision for training 
* -r=\[EventCalculus|Fluent\] use the specified representation for training and testing

#Guide to Modules and their files
We describe the various modules and their python files below:
* DatasetReader
   * bAbI reader: processes story-based Q\&A data files where the data is given in the same format as
    _The (20) QA bAbI tasks dataset_
* en 
  * contains the test and train files for the tasks in _The (20) QA bAbI tasks datasets_. For 
    Task 16 and Task 20, capitalization errors in the tasks have been corrected so that the sentences are 
    grammatically correct.
* Experiments
  * ExpressivityExperiment: contains code for the Expressivity Checker experiment
  * minimumExamplesNeeded: contains code for the Minimum Number of Examples Experiment
  * WeakStrongSupervisionExperiment: contains code for the Supervision experiment
  * GeneralLearningCapabilities: contains code to assess the general learning capabilities of the dataset mode
* Learning Module
  * heuristicGenerator: contains code defining ILASP heuristics for the learning tasks
  * learner: contains the system's learning module
  * modeBiasGenerator: contains the code that generates the mode bias declarations
* Reasoning Module
  * reasoner: contains the system's reasoning module
  * Task16PreferencesInvestigation: contains code that helped us investigate the preferences within bAbI task 16. This 
  file is _not_ needed to run any portion of the system.
* Story Structure
  * Corpus: contains the data structure that encapsulates all stories
  * Question: contains the data structure that encapsulates all questions
  * Sentence: contains the data structure that encapsulates all sentences
  * Story: contains the data structure that encapsulates all stories
* System Pipeline
  * DatasetPipeline: contains the dataset pipeline of the system
  * InteractivePipeline: contains the dialogue pipeline of the system
  * OverallPipeline: contains the overall pipeline of the system. 
* Translational Module
  * BasicParser: contains the code related to the underlying parser for the system
  * ChoiceRulesChecker: contains code that checks if choice rules are present in a corpus
  * ConceptNetIntegration: contains all code related to the system's concept net integration
  * DatasetParser: contains the code related to the dataset parser, which inherits form the basic parser
  * EventCalculus: contains all code related to the Event Calculus logical formalism
  * ExpressivityChecker: contains all code for the system's Expressivity Checker
  * InteractiveParser: contains the code related to the interactive parser, which inherits from the basic parser
* Utilities
  * ILASPSyntax: contains code related to the syntax of ILASP

