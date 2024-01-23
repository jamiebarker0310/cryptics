import pycryptics.puzpy.puz as puz
from pycryptics.solve_clue import CrypticClueSolver
import sys
import readline


def rlinput(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

with CrypticClueSolver() as solver:
    fname = sys.argv[1]
    p = puz.read(fname)

    while True:
        p.print_clue_state()
        action = input("Action? [q]uit [s]ave or enter a clue ID (e.g. 12a): ")
        if action == "q":
            break
        elif action == "s":
            p.save(fname)
        else:
            clue = p.find_clue(action.strip())
            if clue is not None:
                while True:
                    print("Current clue:", p.encode_clue_for_solver(clue))
                    action = input("Clue action? [s]olve [b]ack [g]uess [e]dit: ")
                    if action == "s":
                        solver.setup(p.encode_clue_for_solver(clue))
                        try:
                            answers = solver.run()
                            ans_strings = dict()
                            ans_derivations = dict()
                            ndx = 0
                            for a in answers:
                                if a.answer not in list(ans_strings.values()):
                                    ans_strings[ndx] = a.answer
                                    ndx += 1
                                ans_derivations.setdefault(a.answer, []).append(a)
                            for i in range(min(15, len(list(ans_strings.keys())))):
                                print(i, ans_strings[i])
                            while True:
                                action = input("[a]ccept/[d]erivations [number], or leave blank to cancel: ").strip()
                                if action != "":
                                    try:
                                        verb, noun = action.split(' ')
                                        choice = int(noun)
                                        if verb == "a":
                                            p.set_clue_fill(clue, ans_strings[choice])
                                            break
                                        if verb == "d":
                                            for d in ans_derivations[ans_strings[choice]]:
                                                print(d)
                                    except ValueError:
                                        pass
                        except KeyboardInterrupt:
                            solver.reset()
                    elif action == "b":
                        break
                    elif action == "g":
                        ans = input("Proposed answer: ")
                        p.set_clue_fill(clue, ans)
                        break
                    elif action == "e":
                        clue['clue'] = rlinput("Edited clue: ", clue['clue'])
        # p.save(fname)
