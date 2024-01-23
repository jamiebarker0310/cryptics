
from pycryptics.utils.language import semantic_similarity
from pycryptics.grammar.clue_parse import generate_clues
from pycryptics.utils.phrasings import phrasings
from pycryptics.utils.synonyms import SYNONYMS
from pycryptics.grammar.clue_tree import ClueUnsolvableError
from collections import namedtuple
import re


Constraints = namedtuple('Constraints', 'phrases lengths pattern known_answer')

class AnnotatedAnswer:
    def __init__(self, ans, clue):
        self.answer = ans.encode('ascii', 'replace')
        self.clue = clue
        d_tree = clue[[x.node.name for x in clue].index('d')]
        self.definition = d_tree[0]
        self.similarity = semantic_similarity(self.answer, self.definition)

    def __cmp__(self, other):
        return cmp((self.similarity, self.answer), (other.similarity, other.answer))

    def __str__(self):
        return str([self.answer, self.similarity, self.clue.derivation(self.answer)])

    def derivation(self):
        return "{:.0%}: ".format(self.similarity) + self.clue.derivation(self.answer)

    def long_derivation(self):
        return self.clue.long_derivation(self.answer, self.similarity)


class PatternAnswer(AnnotatedAnswer):
    def __init__(self, ans, phrasing):
        self.answer = ans
        sim0 = semantic_similarity(ans, phrasing[0])
        sim1 = semantic_similarity(ans, phrasing[-1])
        if sim0 > sim1:
            self.definition = phrasing[0]
        else:
            self.definition = phrasing[1]
        self.similarity = max(sim0, sim1)
        self.clue = "???"

    def __str__(self):
        return str([self.answer, self.similarity, self.clue])

    def derivation(self):
        return "???"

    def long_derivation(self):
        return "I don't understand the wordplay for this clue, but {} matches '{}' with confidence score {:.1%}".format(self.answer.upper(), self.definition, self.similarity)

class ClueSolutions:
    def __init__(self, anns):
        self.answer_scores = dict()
        self.answer_derivations = dict()
        for ann in anns:
            self.answer_derivations.setdefault(ann.answer, []).append(ann)
        for k, v in list(self.answer_derivations.items()):
            self.answer_scores[k] = max(a.similarity for a in v)

    def sorted_answers(self):
        return sorted([(v, k) for k, v in list(self.answer_scores.items())], reverse=True)


def arg_filter(arg_set):
    if arg_set != [""]:
        return [a for a in arg_set if not a == ""]
    return arg_set


class CrypticClueSolver(object):
    def __init__(self):
        self.answers_with_clues = None
        self.clue_text = None
        self.quiet = False

    def __enter__(self):
        # self.start_go_server()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()
        # self.stop_go_server()

    def stop(self):
        pass

    def setup(self, clue_text):
        self.clue_text = clue_text

    def run(self):
        self.clue_text = self.clue_text.encode('ascii', 'ignore')
        constraints = parse_clue_text(self.clue_text)
        return self.solve_all_phrasings(constraints)
        # all_phrasings, lengths, pattern, answer = parse_clue_text(self.clue_text)

    def solve_all_phrasings(self, constraints):
        all_phrasings = phrasings(constraints.phrases)

        self.answers_with_clues = []

        for p in all_phrasings:
            constraints = constraints._replace(phrases=p)
            # constraints = Constraints(p, lengths, pattern, answer)
            if not self.quiet:
                print(p)
            for ann_ans in self.solve_constraints(constraints):
                self.answers_with_clues.append(ann_ans)
        if len(self.answers_with_clues) == 0 and constraints.pattern.replace('.', '') != "":
            self.answers_with_clues = [PatternAnswer(x, all_phrasings[0]) for x in SYNONYMS if matches_pattern(x, constraints.pattern, constraints.lengths)]
        self.answers_with_clues.sort(reverse=True)
        return self.answers_with_clues

    def solve_constraints(self, constraints):
        answers_with_clues = []
        possible_clues = generate_clues(constraints)

        for i, clue in enumerate(possible_clues):
            # print "solving:", clue
            try:
                answers = clue.answers
            except ClueUnsolvableError:
                answers = []
            for answer in answers:
                answers_with_clues.append(AnnotatedAnswer(answer, clue))
        return sorted(answers_with_clues, reverse=True)

    def collect_answers(self):
        if self.answers_with_clues is not None:
            return ClueSolutions(self.answers_with_clues)


def matches_pattern(word, pattern, lengths):
    return (tuple(len(x) for x in word.split('_')) == lengths) and all(c == pattern[i] or pattern[i] == '.' for i, c in enumerate(word.replace('_', '')))


def split_clue_text(clue_text):
    clue_text = clue_text.encode('ascii', 'ignore')
    if '|' not in clue_text:
        clue_text += ' |'
    clue_text = clue_text.lower()
    clue, paren, rest = clue_text.rpartition('(')
    lengths, rest = rest.split(')')
    lengths = lengths.replace('-', ',')
    lengths = tuple(int(x) for x in lengths.split(','))
    pattern, answer = rest.split('|')
    pattern = pattern.strip()
    clue = re.sub('-', '_', clue)
    clue = re.sub(r'[^a-zA-Z\ _0-9]', '', clue)
    clue = re.sub(r'\ +', ' ', clue)
    phrases = clue.split(' ')
    phrases = [p for p in phrases if p.strip() != '' and p.strip() != '_']
    return phrases, lengths, pattern, answer


def parse_clue_text(clue_text):
    phrases, lengths, pattern, answer = split_clue_text(clue_text)
    return Constraints(phrases=phrases, lengths=lengths, pattern=pattern,
                       known_answer=answer)
    # return phrasings(phrases), lengths, pattern, answer


if __name__ == '__main__':
    # clue = "spin broken shingle (7)"
    # clue = "sink graduate with sin (5)"
    # clue = "you finally beat iowa perfect world (6)"
    # clue = "be aware of nerd's flip_flop (4) k..."
    # clue = "Bottomless sea, stormy sea - waters' surface rises_and_falls (7) s.es..."
    clue = "gratuitous indicators on_top_of screen (8) n....... | NEEDLESS"
    # phrasing = Phrasing([],(7,),'s.es...')
    # print valid_partial_answer('se', phrasing)
    with CrypticClueSolver() as solver:
        solver.setup(clue)
        answers = solver.run()
        print(answers[0].long_derivation())
        # for a in answers[:5]: print a

