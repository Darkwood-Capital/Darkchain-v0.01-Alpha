#!/usr/bin/env python3.
import random
import gym
import gym.spaces
from collections import namedtuple
import numpy as np
from tensorboardX import SummaryWriter

import torch
import torch.nn as nn
import torch.optim as optim


HIDDEN_SIZE = 128
BATCH_SIZE = 100
PERCENTILE = 30
GAMMA = 0.9


class DiscreteOneHotWrapper(gym.ObservationWrapper):
    def __init__(self, env):
        super(DiscreteOneHotWrapper, self).__init__(env)
        assert isinstance(env.observation_space, gym.spaces.Discrete)
        self.observation_space = gym.spaces.Box(0.0, 1.0, (env.observation_space.n, ), dtype=np.float32)

    def observation(self, observation):
        res = np.copy(self.observation_space.low)
        res[observation] = 1.0
        return res


class Net(nn.Module):
    def __init__(self, obs_size, hidden_size, n_actions):
        super(Net, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, n_actions)
        )

    def forward(self, x):
        return self.net(x)


Episode = namedtuple('Episode', field_names=['reward', 'steps'])
EpisodeStep = namedtuple('EpisodeStep', field_names=['observation', 'action'])


def iterate_batches(env, net, batch_size):
    batch = []
    episode_reward = 0.0
    episode_steps = []
    obs = env.reset()
    sm = nn.Softmax(dim=1)
    while True:
        obs_v = torch.FloatTensor([obs])
        act_probs_v = sm(net(obs_v))
        act_probs = act_probs_v.data.numpy()[0]
        action = np.random.choice(len(act_probs), p=act_probs)
        next_obs, reward, is_done, _ = env.step(action)
        episode_reward += reward
        episode_steps.append(EpisodeStep(observation=obs, action=action))
        if is_done:
            batch.append(Episode(reward=episode_reward, steps=episode_steps))
            episode_reward = 0.0
            episode_steps = []
            next_obs = env.reset()
            if len(batch) == batch_size:
                yield batch
                batch = []
        obs = next_obs


def filter_batch(batch, percentile):
    disc_rewards = list(map(lambda s: s.reward * (GAMMA ** len(s.steps)), batch))
    reward_bound = np.percentile(disc_rewards, percentile)

    train_obs = []
    train_act = []
    elite_batch = []
    for example, discounted_reward in zip(batch, disc_rewards):
        if discounted_reward > reward_bound:
            train_obs.extend(map(lambda step: step.observation, example.steps))
            train_act.extend(map(lambda step: step.action, example.steps))
            elite_batch.append(example)

    return elite_batch, train_obs, train_act, reward_bound


if __name__ == "__main__":
    random.seed(12345)
    env = DiscreteOneHotWrapper(gym.make("FrozenLake-v0"))
    # env = gym.wrappers.Monitor(env, directory="mon", force=True)
    obs_size = env.observation_space.shape[0]
    n_actions = env.action_space.n

    net = Net(obs_size, HIDDEN_SIZE, n_actions)
    objective = nn.CrossEntropyLoss()
    optimizer = optim.Adam(params=net.parameters(), lr=0.001)
    writer = SummaryWriter(comment="-frozenlake-tweaked")

    full_batch = []
    for iter_no, batch in enumerate(iterate_batches(env, net, BATCH_SIZE)):
        reward_mean = float(np.mean(list(map(lambda s: s.reward, batch))))
        full_batch, obs, acts, reward_bound = filter_batch(full_batch + batch, PERCENTILE)
        if not full_batch:
            continue
        obs_v = torch.FloatTensor(obs)
        acts_v = torch.LongTensor(acts)
        full_batch = full_batch[-500:]

        optimizer.zero_grad()
        action_scores_v = net(obs_v)
        loss_v = objective(action_scores_v, acts_v)
        loss_v.backward()
        optimizer.step()
        print("%d: loss=%.3f, reward_mean=%.3f, reward_bound=%.3f, batch=%d" % (
            iter_no, loss_v.item(), reward_mean, reward_bound, len(full_batch)))
        writer.add_scalar("loss", loss_v.item(), iter_no)
        writer.add_scalar("reward_mean", reward_mean, iter_no)
        writer.add_scalar("reward_bound", reward_bound, iter_no)
        if reward_mean > 0.8:
            print("Solved!")
            break
    writer.close()
    
   //////
  
  
  #!/usr/bin/env python3
import random
import gym
import gym.spaces
import gym.wrappers
import gym.envs.toy_text.frozen_lake
from collections import namedtuple
import numpy as np
from tensorboardX import SummaryWriter

import torch
import torch.nn as nn
import torch.optim as optim


HIDDEN_SIZE = 128
BATCH_SIZE = 100
PERCENTILE = 30
GAMMA = 0.9


class DiscreteOneHotWrapper(gym.ObservationWrapper):
    def __init__(self, env):
        super(DiscreteOneHotWrapper, self).__init__(env)
        assert isinstance(env.observation_space, gym.spaces.Discrete)
        self.observation_space = gym.spaces.Box(0.0, 1.0, (env.observation_space.n, ), dtype=np.float32)

    def observation(self, observation):
        res = np.copy(self.observation_space.low)
        res[observation] = 1.0
        return res


class Net(nn.Module):
    def __init__(self, obs_size, hidden_size, n_actions):
        super(Net, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, n_actions)
        )

    def forward(self, x):
        return self.net(x)


Episode = namedtuple('Episode', field_names=['reward', 'steps'])
EpisodeStep = namedtuple('EpisodeStep', field_names=['observation', 'action'])


def iterate_batches(env, net, batch_size):
    batch = []
    episode_reward = 0.0
    episode_steps = []
    obs = env.reset()
    sm = nn.Softmax(dim=1)
    while True:
        obs_v = torch.FloatTensor([obs])
        act_probs_v = sm(net(obs_v))
        act_probs = act_probs_v.data.numpy()[0]
        action = np.random.choice(len(act_probs), p=act_probs)
        next_obs, reward, is_done, _ = env.step(action)
        episode_reward += reward
        episode_steps.append(EpisodeStep(observation=obs, action=action))
        if is_done:
            batch.append(Episode(reward=episode_reward, steps=episode_steps))
            episode_reward = 0.0
            episode_steps = []
            next_obs = env.reset()
            if len(batch) == batch_size:
                yield batch
                batch = []
        obs = next_obs


def filter_batch(batch, percentile):
    disc_rewards = list(map(lambda s: s.reward * (GAMMA ** len(s.steps)), batch))
    reward_bound = np.percentile(disc_rewards, percentile)

    train_obs = []
    train_act = []
    elite_batch = []
    for example, discounted_reward in zip(batch, disc_rewards):
        if discounted_reward > reward_bound:
            train_obs.extend(map(lambda step: step.observation, example.steps))
            train_act.extend(map(lambda step: step.action, example.steps))
            elite_batch.append(example)

    return elite_batch, train_obs, train_act, reward_bound


if __name__ == "__main__":
    random.seed(12345)
    env = gym.envs.toy_text.frozen_lake.FrozenLakeEnv(is_slippery=False)
    env = gym.wrappers.TimeLimit(env, max_episode_steps=100)
    env = DiscreteOneHotWrapper(env)
    # env = gym.wrappers.Monitor(env, directory="mon", force=True)
    obs_size = env.observation_space.shape[0]
    n_actions = env.action_space.n

    net = Net(obs_size, HIDDEN_SIZE, n_actions)
    objective = nn.CrossEntropyLoss()
    optimizer = optim.Adam(params=net.parameters(), lr=0.001)
    writer = SummaryWriter(comment="-frozenlake-nonslippery")

    full_batch = []
    for iter_no, batch in enumerate(iterate_batches(env, net, BATCH_SIZE)):
        reward_mean = float(np.mean(list(map(lambda s: s.reward, batch))))
        full_batch, obs, acts, reward_bound = filter_batch(full_batch + batch, PERCENTILE)
        if not full_batch:
            continue
        obs_v = torch.FloatTensor(obs)
        acts_v = torch.LongTensor(acts)
        full_batch = full_batch[-500:]

        optimizer.zero_grad()
        action_scores_v = net(obs_v)
        loss_v = objective(action_scores_v, acts_v)
        loss_v.backward()
        optimizer.step()
        print("%d: loss=%.3f, reward_mean=%.3f, reward_bound=%.3f, batch=%d" % (
            iter_no, loss_v.item(), reward_mean, reward_bound, len(full_batch)))
        writer.add_scalar("loss", loss_v.item(), iter_no)
        writer.add_scalar("reward_mean", reward_mean, iter_no)
        writer.add_scalar("reward_bound", reward_bound, iter_no)
        if reward_mean > 0.8:
            print("Solved!")
            break
    writer.close()
    
    //////
    
    #!/usr/bin/env python3
import gym
import collections
from tensorboardX import SummaryWriter

ENV_NAME = "FrozenLake-v0"
GAMMA = 0.9
ALPHA = 0.2
TEST_EPISODES = 20


class Agent:
    def __init__(self):
        self.env = gym.make(ENV_NAME)
        self.state = self.env.reset()
        self.values = collections.defaultdict(float)

    def sample_env(self):
        action = self.env.action_space.sample()
        old_state = self.state
        new_state, reward, is_done, _ = self.env.step(action)
        self.state = self.env.reset() if is_done else new_state
        return (old_state, action, reward, new_state)

    def best_value_and_action(self, state):
        best_value, best_action = None, None
        for action in range(self.env.action_space.n):
            action_value = self.values[(state, action)]
            if best_value is None or best_value < action_value:
                best_value = action_value
                best_action = action
        return best_value, best_action

    def value_update(self, s, a, r, next_s):
        best_v, _ = self.best_value_and_action(next_s)
        new_val = r + GAMMA * best_v
        old_val = self.values[(s, a)]
        self.values[(s, a)] = old_val * (1-ALPHA) + new_val * ALPHA

    def play_episode(self, env):
        total_reward = 0.0
        state = env.reset()
        while True:
            _, action = self.best_value_and_action(state)
            new_state, reward, is_done, _ = env.step(action)
            total_reward += reward
            if is_done:
                break
            state = new_state
        return total_reward


if __name__ == "__main__":
    test_env = gym.make(ENV_NAME)
    agent = Agent()
    writer = SummaryWriter(comment="-q-learning")

    iter_no = 0
    best_reward = 0.0
    while True:
        iter_no += 1
        s, a, r, next_s = agent.sample_env()
        agent.value_update(s, a, r, next_s)

        reward = 0.0
        for _ in range(TEST_EPISODES):
            reward += agent.play_episode(test_env)
        reward /= TEST_EPISODES
        writer.add_scalar("reward", reward, iter_no)
        if reward > best_reward:
            print("Best reward updated %.3f -> %.3f" % (best_reward, reward))
            best_reward = reward
        if reward > 0.80:
            print("Solved in %d iterations!" % iter_no)
            break
    writer.close()
    
    ////
    
    %!PS-Adobe-3.0 EPSF-3.0
%Produced by poppler pdftops version: 0.57.0 (http://poppler.freedesktop.org)
%%Creator: TeX
%%LanguageLevel: 2
%%DocumentSuppliedResources: (atend)
%%BoundingBox: 0 0 345 32
%%HiResBoundingBox: 0 0 344.711 31.428
%%DocumentSuppliedResources: (atend)
%%EndComments
%%BeginProlog
%%BeginResource: procset xpdf 3.00 0
%%Copyright: Copyright 1996-2011 Glyph & Cog, LLC
/xpdf 75 dict def xpdf begin
% PDF special state
/pdfDictSize 15 def
/pdfSetup {
  /setpagedevice where {
    pop 2 dict begin
      /Policies 1 dict dup begin /PageSize 6 def end def
      { /Duplex true def } if
    currentdict end setpagedevice
  } {
    pop
  } ifelse
} def
/pdfSetupPaper {
  % Change paper size, but only if different from previous paper size otherwise
  % duplex fails. PLRM specifies a tolerance of 5 pts when matching paper size
  % so we use the same when checking if the size changes.
  /setpagedevice where {
    pop currentpagedevice
    /PageSize known {
      2 copy
      currentpagedevice /PageSize get aload pop
      exch 4 1 roll
      sub abs 5 gt
      3 1 roll
      sub abs 5 gt
      or
    } {
      true
    } ifelse
    {
      2 array astore
      2 dict begin
        /PageSize exch def
        /ImagingBBox null def
      currentdict end
      setpagedevice
    } {
      pop pop
    } ifelse
  } {
    pop
  } ifelse
} def
/pdfStartPage {
  pdfDictSize dict begin
  /pdfFillCS [] def
  /pdfFillXform {} def
  /pdfStrokeCS [] def
  /pdfStrokeXform {} def
  /pdfFill [0] def
  /pdfStroke [0] def
  /pdfFillOP false def
  /pdfStrokeOP false def
  /pdfLastFill false def
  /pdfLastStroke false def
  /pdfTextMat [1 0 0 1 0 0] def
  /pdfFontSize 0 def
  /pdfCharSpacing 0 def
  /pdfTextRender 0 def
  /pdfPatternCS false def
  /pdfTextRise 0 def
  /pdfWordSpacing 0 def
  /pdfHorizScaling 1 def
  /pdfTextClipPath [] def
} def
/pdfEndPage { end } def
% PDF color state
/cs { /pdfFillXform exch def dup /pdfFillCS exch def
      setcolorspace } def
/CS { /pdfStrokeXform exch def dup /pdfStrokeCS exch def
      setcolorspace } def
/sc { pdfLastFill not { pdfFillCS setcolorspace } if
      dup /pdfFill exch def aload pop pdfFillXform setcolor
     /pdfLastFill true def /pdfLastStroke false def } def
/SC { pdfLastStroke not { pdfStrokeCS setcolorspace } if
      dup /pdfStroke exch def aload pop pdfStrokeXform setcolor
     /pdfLastStroke true def /pdfLastFill false def } def
/op { /pdfFillOP exch def
      pdfLastFill { pdfFillOP setoverprint } if } def
/OP { /pdfStrokeOP exch def
      pdfLastStroke { pdfStrokeOP setoverprint } if } def
/fCol {
  pdfLastFill not {
    pdfFillCS setcolorspace
    pdfFill aload pop pdfFillXform setcolor
    pdfFillOP setoverprint
    /pdfLastFill true def /pdfLastStroke false def
  } if
} def
/sCol {
  pdfLastStroke not {
    pdfStrokeCS setcolorspace
    pdfStroke aload pop pdfStrokeXform setcolor
    pdfStrokeOP setoverprint
    /pdfLastStroke true def /pdfLastFill false def
  } if
} def
% build a font
/pdfMakeFont {
  4 3 roll findfont
  4 2 roll matrix scale makefont
  dup length dict begin
    { 1 index /FID ne { def } { pop pop } ifelse } forall
    /Encoding exch def
    currentdict
  end
  definefont pop
} def
/pdfMakeFont16 {
  exch findfont
  dup length dict begin
    { 1 index /FID ne { def } { pop pop } ifelse } forall
    /WMode exch def
    currentdict
  end
  definefont pop
} def
% graphics state operators
/q { gsave pdfDictSize dict begin } def
/Q {
  end grestore
  /pdfLastFill where {
    pop
    pdfLastFill {
      pdfFillOP setoverprint
    } {
      pdfStrokeOP setoverprint
    } ifelse
  } if
} def
/cm { concat } def
/d { setdash } def
/i { setflat } def
/j { setlinejoin } def
/J { setlinecap } def
/M { setmiterlimit } def
/w { setlinewidth } def
% path segment operators
/m { moveto } def
/l { lineto } def
/c { curveto } def
/re { 4 2 roll moveto 1 index 0 rlineto 0 exch rlineto
      neg 0 rlineto closepath } def
/h { closepath } def
% path painting operators
/S { sCol stroke } def
/Sf { fCol stroke } def
/f { fCol fill } def
/f* { fCol eofill } def
% clipping operators
/W { clip newpath } def
/W* { eoclip newpath } def
/Ws { strokepath clip newpath } def
% text state operators
/Tc { /pdfCharSpacing exch def } def
/Tf { dup /pdfFontSize exch def
      dup pdfHorizScaling mul exch matrix scale
      pdfTextMat matrix concatmatrix dup 4 0 put dup 5 0 put
      exch findfont exch makefont setfont } def
/Tr { /pdfTextRender exch def } def
/Tp { /pdfPatternCS exch def } def
/Ts { /pdfTextRise exch def } def
/Tw { /pdfWordSpacing exch def } def
/Tz { /pdfHorizScaling exch def } def
% text positioning operators
/Td { pdfTextMat transform moveto } def
/Tm { /pdfTextMat exch def } def
% text string operators
/xyshow where {
  pop
  /xyshow2 {
    dup length array
    0 2 2 index length 1 sub {
      2 index 1 index 2 copy get 3 1 roll 1 add get
      pdfTextMat dtransform
      4 2 roll 2 copy 6 5 roll put 1 add 3 1 roll dup 4 2 roll put
    } for
    exch pop
    xyshow
  } def
}{
  /xyshow2 {
    currentfont /FontType get 0 eq {
      0 2 3 index length 1 sub {
        currentpoint 4 index 3 index 2 getinterval show moveto
        2 copy get 2 index 3 2 roll 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } {
      0 1 3 index length 1 sub {
        currentpoint 4 index 3 index 1 getinterval show moveto
        2 copy 2 mul get 2 index 3 2 roll 2 mul 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } ifelse
    pop pop
  } def
} ifelse
/cshow where {
  pop
  /xycp {
    0 3 2 roll
    {
      pop pop currentpoint 3 2 roll
      1 string dup 0 4 3 roll put false charpath moveto
      2 copy get 2 index 2 index 1 add get
      pdfTextMat dtransform rmoveto
      2 add
    } exch cshow
    pop pop
  } def
}{
  /xycp {
    currentfont /FontType get 0 eq {
      0 2 3 index length 1 sub {
        currentpoint 4 index 3 index 2 getinterval false charpath moveto
        2 copy get 2 index 3 2 roll 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } {
      0 1 3 index length 1 sub {
        currentpoint 4 index 3 index 1 getinterval false charpath moveto
        2 copy 2 mul get 2 index 3 2 roll 2 mul 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } ifelse
    pop pop
  } def
} ifelse
/Tj {
  fCol
  0 pdfTextRise pdfTextMat dtransform rmoveto
  currentpoint 4 2 roll
  pdfTextRender 1 and 0 eq {
    2 copy xyshow2
  } if
  pdfTextRender 3 and dup 1 eq exch 2 eq or {
    3 index 3 index moveto
    2 copy
    currentfont /FontType get 3 eq { fCol } { sCol } ifelse
    xycp currentpoint stroke moveto
  } if
  pdfTextRender 4 and 0 ne {
    4 2 roll moveto xycp
    /pdfTextClipPath [ pdfTextClipPath aload pop
      {/moveto cvx}
      {/lineto cvx}
      {/curveto cvx}
      {/closepath cvx}
    pathforall ] def
    currentpoint newpath moveto
  } {
    pop pop pop pop
  } ifelse
  0 pdfTextRise neg pdfTextMat dtransform rmoveto
} def
/TJm { 0.001 mul pdfFontSize mul pdfHorizScaling mul neg 0
       pdfTextMat dtransform rmoveto } def
/TJmV { 0.001 mul pdfFontSize mul neg 0 exch
        pdfTextMat dtransform rmoveto } def
/Tclip { pdfTextClipPath cvx exec clip newpath
         /pdfTextClipPath [] def } def
/Tclip* { pdfTextClipPath cvx exec eoclip newpath
         /pdfTextClipPath [] def } def
% Level 2/3 image operators
/pdfImBuf 100 string def
/pdfImStr {
  2 copy exch length lt {
    2 copy get exch 1 add exch
  } {
    ()
  } ifelse
} def
/skipEOD {
  { currentfile pdfImBuf readline
    not { pop exit } if
    (%-EOD-) eq { exit } if } loop
} def
/pdfIm { image skipEOD } def
/pdfImM { fCol imagemask skipEOD } def
/pr { 2 index 2 index 3 2 roll putinterval 4 add } def
/pdfImClip {
  gsave
  0 2 4 index length 1 sub {
    dup 4 index exch 2 copy
    get 5 index div put
    1 add 3 index exch 2 copy
    get 3 index div put
  } for
  pop pop rectclip
} def
/pdfImClipEnd { grestore } def
% shading operators
/colordelta {
  false 0 1 3 index length 1 sub {
    dup 4 index exch get 3 index 3 2 roll get sub abs 0.004 gt {
      pop true
    } if
  } for
  exch pop exch pop
} def
/funcCol { func n array astore } def
/funcSH {
  dup 0 eq {
    true
  } {
    dup 6 eq {
      false
    } {
      4 index 4 index funcCol dup
      6 index 4 index funcCol dup
      3 1 roll colordelta 3 1 roll
      5 index 5 index funcCol dup
      3 1 roll colordelta 3 1 roll
      6 index 8 index funcCol dup
      3 1 roll colordelta 3 1 roll
      colordelta or or or
    } ifelse
  } ifelse
  {
    1 add
    4 index 3 index add 0.5 mul exch 4 index 3 index add 0.5 mul exch
    6 index 6 index 4 index 4 index 4 index funcSH
    2 index 6 index 6 index 4 index 4 index funcSH
    6 index 2 index 4 index 6 index 4 index funcSH
    5 3 roll 3 2 roll funcSH pop pop
  } {
    pop 3 index 2 index add 0.5 mul 3 index  2 index add 0.5 mul
    funcCol sc
    dup 4 index exch mat transform m
    3 index 3 index mat transform l
    1 index 3 index mat transform l
    mat transform l pop pop h f*
  } ifelse
} def
/axialCol {
  dup 0 lt {
    pop t0
  } {
    dup 1 gt {
      pop t1
    } {
      dt mul t0 add
    } ifelse
  } ifelse
  func n array astore
} def
/axialSH {
  dup 0 eq {
    true
  } {
    dup 8 eq {
      false
    } {
      2 index axialCol 2 index axialCol colordelta
    } ifelse
  } ifelse
  {
    1 add 3 1 roll 2 copy add 0.5 mul
    dup 4 3 roll exch 4 index axialSH
    exch 3 2 roll axialSH
  } {
    pop 2 copy add 0.5 mul
    axialCol sc
    exch dup dx mul x0 add exch dy mul y0 add
    3 2 roll dup dx mul x0 add exch dy mul y0 add
    dx abs dy abs ge {
      2 copy yMin sub dy mul dx div add yMin m
      yMax sub dy mul dx div add yMax l
      2 copy yMax sub dy mul dx div add yMax l
      yMin sub dy mul dx div add yMin l
      h f*
    } {
      exch 2 copy xMin sub dx mul dy div add xMin exch m
      xMax sub dx mul dy div add xMax exch l
      exch 2 copy xMax sub dx mul dy div add xMax exch l
      xMin sub dx mul dy div add xMin exch l
      h f*
    } ifelse
  } ifelse
} def
/radialCol {
  dup t0 lt {
    pop t0
  } {
    dup t1 gt {
      pop t1
    } if
  } ifelse
  func n array astore
} def
/radialSH {
  dup 0 eq {
    true
  } {
    dup 8 eq {
      false
    } {
      2 index dt mul t0 add radialCol
      2 index dt mul t0 add radialCol colordelta
    } ifelse
  } ifelse
  {
    1 add 3 1 roll 2 copy add 0.5 mul
    dup 4 3 roll exch 4 index radialSH
    exch 3 2 roll radialSH
  } {
    pop 2 copy add 0.5 mul dt mul t0 add
    radialCol sc
    encl {
      exch dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      0 360 arc h
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      360 0 arcn h f
    } {
      2 copy
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a1 a2 arcn
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a2 a1 arcn h
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a1 a2 arc
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a2 a1 arc h f
    } ifelse
  } ifelse
} def
end
%%EndResource
%%EndProlog
%%BeginSetup
xpdf begin
%%BeginResource: font YQYTWD+CMMI10
%!PS-AdobeFont-1.0: CMMI10 003.002
%%Title: CMMI10
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMMI10.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMMI10 known{/CMMI10 findfont dup/UniqueID known{dup
/UniqueID get 5087385 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /YQYTWD+CMMI10 def
/FontBBox {-32 -250 1048 750 }readonly def
/PaintType 0 def
/FontInfo 10 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMMI10.) readonly def
/FullName (CMMI10) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle -14.04 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
/ascent 750 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 65 /A put
dup 71 /G put
dup 80 /P put
dup 82 /R put
dup 83 /S put
dup 86 /V put
dup 97 /a put
dup 13 /gamma put
dup 58 /period put
dup 25 /pi put
dup 115 /s put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3c05ef98f858322dcea45e0874c5
45d25fe192539d9cda4baa46d9c431465e6abf4e4271f89eded7f37be4b31fb4
7934f62d1f46e8671f6290d6fff601d4937bf71c22d60fb800a15796421e3aa7
72c500501d8b10c0093f6467c553250f7c27b2c3d893772614a846374a85bc4e
bec0b0a89c4c161c3956ece25274b962c854e535f418279fe26d8f83e38c5c89
974e9a224b3cbef90a9277af10e0c7cac8dc11c41dc18b814a7682e5f0248674
11453bc81c443407af56dca20efc9fa776eb9a127b62471340eb64c5abdf2996
f8b24ef268e4f2eb5d212894c037686094668c31ec7af91d1170dc14429872a0
a3e68a64db9e871f03b7c73e93f77356c3996948c2deade21d6b4a87854b79da
d4c3d1e0fc754b97495bcfc684282c4d923dfeace4ec7db525bd8d76668602ba
27b09611e4452b169c29ea7d6683a2c6246c9ddcf62885d457325b389868bc54
3ea6dc3984ba80581133330d766998ae550e2fb5e7c707a559f67b7a34fea2f3
bebe4226da71af8b6e8d128c7ae0b3dc7c9aa4a1faef312fc9b46399b18c437a
776de1f67caf78e15d4cc76d6fa57dad7abc6d35ede0d7118e8c6f3a201f9ea9
eabf8a848d182eba8922addbe3c488f51eac02906400a84ea0abfaf48116cdc6
6fbc00330a76a8818cfaeb7afdeb029a204e0a70b47a05aa50153b56d2bf6736
c7a2c50b023ed92cfff13eba974f804a346d4130ccfd5233b6d6b92a14c87bbe
2ba216bae4123911e1856975e5cf4d94e44f400f687d2d13db288e0d821451c8
83e9928f8cbc41e0f4b99f8b29d3b11bd4ed0cbca83d81082e39a9e79cebf433
671b1af39c3d0e1f5bbe5f1fff62ff6f5f15f0421c56a4dffac682cb07b6f257
221fed1902e4b69d9bc2e061f2e96f5a46734f91298494a425ef6432f2b9778c
4ebbadd3483ef5447df5f008db9d91c559950ebcedb4b1316a5aae8367a80e06
bf3162beb99c4aaa617c60be688da7627f29c1775983ef635b26306a94f0b258
003779f8670a1398681953b785a226057f7d1270fe2dd2ea66d65e2061fbd65f
0ac51b6c347a56e9f3e86e52f3e0bf1d5f8d6540afb32a027a7c96919557692e
b739cc298ec7999b4286538edf7333cf8f8f6ba02c5e8c62929af07acbb90861
0bcb85345f4206e3ea130512dcfbc6cefa31ef2bd1da11d3010fec57b5b232ca
706f9c44fb9cab8903be783eca66d748b3fa5b1f5d5445f6c16a9a52c88a7e2f
2bfb0be4e416ea209a9810dd6c38e47a58dc9270b2f49f9b9d482156f7dc8164
b621b6803b6434a2a354a50fd9353a2ce3fa761423634b8f2adcd63b2b7acf15
07588caf127a0d6b2017a451d3df77c53e6171c66236e5318d49fab9ce4b1026
853f65d0d5f7913d88ea66b9b63cf06a4bfc8ed3246bb86cf6de255ff46d245d
109939e32dc483a0e5176b614ccb7f1adcf99854cf50317bd081131a146ea089
8ed59e46da7b6254bdccbc660686e2eda0ad7b894cd2eb2688c0c00aca589d39
e3caa6e0faf7eeb5df3e3f8113dae4b454a0d8c86fee52779ad3e13a0a871e9b
65b9ef0a2ff20989bae81d1cc1181679fbedb80e7d84a08774e6da58a283ba22
3780f2717484e066fa7dc012e6d19429b08638045352d358957917123c9c73b4
326a954f5ebce183ba1025c00c8f559dba85e07b3ed48d2fa0acafa9436d6fdf
e530ce25ac7da170db1764e77b6816343e8a128a075e7744a6f0406551f4640e
c403ea61696459d15ee040bfb53f08700c69333b1cb28142c5b9411d65fbfb1e
c7f4f50c03d122ad4b63e9e65f0a0af43efcc9fc546fd13da42a1c13b8c9cbfa
79a480d923701306249955ce1c61a680b2809d3551325a333a189db71bc83c59
47d17b31f8ff63564919b00336285f724d22f889748564808083ddaa4eeb8632
5d636961e1f634f3ff3def1dcd7299bb7679dbaf685e2ac1484bd9b17c5cf4d8
59897713b51a4deba3332c2ab5c48a76357d2eaaa539a617b09f223661bcb411
0e6559e99a7d900336a9327d4b8330ee5f56b016cebb8c07dbcc2fa736c07ecb
8930f26b429288c6fe6cee3e7792de58ea3ce248598db0c604787612bd137d80
e4462d249b229b62142128b57a6b44515262743bb3c70ee96aa4b8c49d6b0be4
4e19f634add30634f999f4dfb3dcff6a412a9b6067d28751aab1b20928a6e73b
cb81b0510d551f84437062e8cd403bf8c343003965e926465b288b0aa2fc85f9
90f9a63fce188d72008aed98bcba5ff4ae850711d2664f0857ded002e3a89fa8
75f930ddf7918d6b2f92ae26af35f50cc9d2a8f9b5d5d80981b12ddf4c59565a
aa62ec34589e5bcc3075cc6a163e45d46bb280b22158c5c04c90beb6f8a1c791
5597b0f69be3204d876cfa54481cc86ed2fe799bc46555c6c6fffc73854104dc
9c8a6f85331fce7c5d1f20af5d99e4e61b7ab981dd4eae26951a9447d5553140
b5862e2f39023bc7d14901eacf467a9424a6be8055d82f4b02036cd766367871
e0a01d09790ab2777db18248482fb32a25fadb62956b93affc59b1796f78d0b6
6aaeee9778a3b253bd98035c79b5296e173fba9e56e8824ab6191ef9062b1fc8
1b6b6185a05b167adccc6698b1801297d766492add5b66193d024d121633d329
25bcf1a9ae109371aaaeb64f2805bf5c2d5a218c191e9eeb4ac30a48291c7251
f690b51d5135f6a37f5418624c7d2f3ece356b12ec18f73d5177a24ffe371635
fc88231b3a95d72ca2555f164c503f91b5c7ca174e43aee6534df6d569efd50d
da3e950e11c6cff788e50ce5f1332ad76a2357c39d44ea38e88b24f2d37cf29e
21b7468adfcacc8ab8fe1ae9da4c933b5f7f0a6451964a4924b6ba96c359c828
d818166d5271e813f7a34a5b18927e66d61003392c96ab36b3e2175f31faa3d3
7e77200bbbeba91c532c053f318f3f83080bf3d641d4c5df796c2882e34c01b9
cf74bba01f03ef559012eeece809c019ab6d40d22a16fb9054143990db45b902
a5574f672dda96d6c18c0fb048e970e6180e6148061e22085c7aa4fdc2102fd2
d31e84456a56057b9d3189f331cc8354b195564cfdd23579574b7c7a80d2f3e3
97f07cdab67407a46a4264e985563dae7ad933dac054d64a7ebce65bb2beb5fe
d53360fd76a0fe706e7283550c4d5657aa9bf62ee713592d74e89998e9b0adb2
327a9dd5f19184a500870a3c53367431b56cc4dd60bb629ae68a009fba0049eb
16d11d5f299d5a99f3d45f6510450e53740da5556335eccd43e1408b826fc535
10c7784c44cdbf41988ab67ffdc54ea61dd05208204c8bed9c66c678e6324428
9682cc6ea0b2dad69cdb69dc8daacfd1a98c730dc3d9bc8d83e2fa2e72de08b0
031ef3455ba92d03acfdb7ecf50ee883a8817abd96e58f72ae050feae0d224a5
42aa0b4c022f8a90e73ab84216f520d6ded72680471b9ed2ce317536305d7360
810a92f4957c9aba9328b116349fdfa728e9f042b2fd2d116bbcbbb99ec6966b
a5e1f4fbbb4b1eae6d8bdd40de5fa44127e6d7c05abad3c012082c245265096d
d4445b03ad8dc08d707ecbf0aef0890b0658dc9341fd386d417ad9f5e79c0464
be4e3b22e4997e1806d192a8be70dfbcf69715b8194347a60e80934ed09fb08e
c4df7c3b204b07ee3610c041dff7d4c76060e4be6a3a2f0b0217005ab38f80ff
fe55a6252afa361b5cd8f3b642e6e193da913ccaeae5508c2470036aad80c0c6
e977c374852b69a8de69aea44aaad49eb7fcd420bd55a5c5cbf073e859ba9d6a
857da20a5cc2744843ea07efcaf91e992f0a44e1e520bbca097b6965c4e30c99
03ac3ca1af1bbeeacffd7cc22e7b9763b0876cf8308ea38828a716da7f430898
2beecd1cb81cd95ab8fe70242026f11061a70fb42445aa9246488d6d0029df17
dea43305ac74df52e5699b6c243025786b21fd43993a8039e9e75fce2dbb7d6b
7e4cd140e7edacc20dcb473dc45eab68d8ea296baf9bb969093862d391f84073
5e17f87847ff2e9186080feb184ff7869a5a8bee6aafe3461454dcbcd00d2c24
61ef831a52dbb0fa736694b4a3a4d85c6d80636b316fb12be67f0887cce6df04
80c145ea8762ef8b2c43ae71f3c32686fd5813eb49a39bc6d4980472bd5cdbb6
c282c9ffe2fb52656f607692e1ba726417703feccfd4aeaf9c66d543ce1506b1
a9d6b95705f67086d4f36b06a283cec841a01f1028d95d4de419d7110f091014
f6dc905e81add1d54f95b16cddcfd0793d1cf4a85e7a35458c81197a24fe82cb
63edde30cb6b538a708fbd41f00268a772730b85bd8860054acd93fe6b8bbcb9
cc474568d426e83f15838520a313e0ae1b60959de340398b21986f5c404c9361
54975d52740bec0f7abfaf271a2ac1f7553b862d45d11ae585936fbb5462e2dd
bf35e4afb7bffcbd3294be3eabec4b787133c3a5e0c95f74a71dad9be990d07c
d157d7258830a3cc3de6459140afba942eef325ee072b3a53a9f281d483eac65
e8da50ccddb3d43baff7d8c7d7a1847d6d579ce92df1b54de141ce7a73607362
7d909e8cd9fdc373b840145f9373bc2f02979ee34688bf840f4f9245c2ab976c
ee8bde685c47606201f6611e38a49ab72428def2c85e553313af719ab4d4f5ef
e3f3430522abff76bf8bb8f56afe11008d3f989ffadccb411dd3b7e6352ea873
3abe5dc71b3b4832ae85bdb23f6cbfb4b2631412e4fe0050a5f7f4216508a3db
ea2d74318ed82f1a2fc791623c869593dcfd6bfb2fe57bdf06e9d1946f9bcea0
13848fcdc603e3eca5384725118970cebcc9ebc6b74df13ad395fa6efdc22463
5380eb1b3521aa929eba30958ae2da40852196b67ee44409d323383b0c7fa1f2
b4fff373041d9f5eeab03d6743f0a291b481dd3ff9e8ebd77a073b8d5f5d93bc
727e6566204893af892f74fc0bc3f3e83643a93747678eb998f9c91b3a0ff942
3d3924f507f1c7eb18249b2ab73691f5fac868720ff52183091f65ac3be8cb0e
80d257c52ea8647ef747fe304598e1ce0900a4de4031e4b6a58d7869b08a56aa
710c91ccb8afab94ad10d670e767a44e0177795ddfd65c9cdc7332716deefe3f
9e2ed8a54bb6faf63b7bf5f554b934821086c09fc28fa74ea2efd410e006be6b
ebe0c464e078c14968453dc783a788a55d925d72205492c07d0dbaee4982fbed
9b32dd19ae230da5870499feeac55b09b0970ad5926375fd79b95552816be003
90515262b5ca891babcd81bf86847cbc5850d4a056bdc528e97aded1ea6d7b76
bd8ec34e742a9fccf19a6310004499b1cc1a920b5f3b746bd4de2d9b9dea341d
25a7a7b60546a8f9ef99190cf8ddedb21a0103414f9f28ae8673c966b12528dc
fb70ce44db4822322605982d708a0b4bef7eb08962e3f433213d7545f351e994
970828eb443c3bb36ab0c4cab7fadfd949e5f93273141da2b6dffb41b4678647
93cd4e53c78a63c632d4fcbad772122e86dde337d5438e5e4342a0e18be8b014
3ddd7290d16096f2149c6c71ad28325dddbf994e651b9d4be89430b31dec3fa7
d2703196f7f10b5e8d98f20e14151160507e53ff1f3d4bddff3f45f9e64b1b9b
9b26b32bf389a3725c243209245bd78c2f78d67033be00ebe25955a1ac718305
b52a0260a07220a9f7410bad935538c6c7c56f902a70730c1cf90d45a5f66c6b
a762406e512bf3cc3b52918c6e9e92893279cf86af1684d9b67d1ebbe84be9d8
4b56548323ab381ae18c9e9570453abe77ca9d9ed1164563120b939fc3acc33d
49f5e989a74ac760f0c99458295278efde92e99003c4780935d12eda68a82308
ba444819ea9fd930c80263b57ec1b9164aa50ce386b8ef81a53a710416c6c868
794bddb4fe463b3c59ff9fd085fc7ec37cf2abb7df09d41113f4542f72bffda6
1fafef41c462eabcc7a3b4fbe46cac256c7af4309a617e73e7934450434e344b
5cb6ddf2e63f4523f1526ed2f79522eae16b23dd9ff4924053a0fa7c4a0b29ff
f4485c041b06147d2c94d276553f443c2980cb96ef5da49bfda4ee95bbf092ac
e2dee947d0c711c1930500b79a5424e8494df6e1798b009a3816342f4d1d7cb0
b7bf239f3d60361ac605020591740d13ce386bca1e69a2e8063c62f9959c9fb9
010ae39f18882b1e3b3d0d9b0447db7f7f7a3810375372702686b224896bf5e4
cd40e308b5a6988b614d8088c296171423cab2657cfb98f462afe21e990b0c74
4c8738d1b13097ca887ccfd3eabe4f1e29df71d0e51046957409964f9f02a33d
78b2a5bac5058bda0dd8a65fe6c53dff9310fd2b97afd24f39e586417dcc18a1
5c0be1795e0f2c3d785f8cc1ab5505bb8fc0dfa1364f08876a42dae3383f853f
84e7e54405bb8d00911c5b8ef4794494d9bf076d57a65f2392628b61ff967c77
29114960e00fadc36961617c61c673bd2d2e4a9d54702233c8414026e67940bd
ed16e2d3822f06068502c0966f2ff68f74d11a0b780b95f3f52bcc162a37b6ef
48cf5ff8513cf4183176734f80b9835401b3db6bd53597645873fa96488eb183
646b577037e5717952d23cc71ee1780b3df42d9c768804fc47cf147db059b9ee
7a6399d4f4afcf2d296902f16d56d6df28ac4c9a96e357678ba901fe72ce3d2f
b10fbf263146547d455df1bc33a1dfa753251c264db8798da35943a4940962f9
e3b8a68d2b094177154ba30af7bd201cad919c09a34536e41d6c5772873c0634
fef84dca5f1a5d5488997e279876af1dfb3f51790a6ae085d09ea4e1947fc10b
987c2db0634c100484f4b45404119fee7a7ec81111029cff1b4cfa1a8637d4a5
ad472b5ac0cb9f428cb1df8abfea3db8082a26cc815437ab387e7f87902398d2
e0c6bf6c95c2381f15b61fb2c5bdb8684afbb7a6c1a01ca2286a8dff62e52a16
3d7c748c1b2c63d2933012c5306cb7efb0b4cd733c56ba7700acc731d294f7a1
1f2a1f8f461983f2972da8c3dbb3f9117f7a6f3583c8a5dcabb364ac0310457f
93fbca26c31482d806c6a7a4f87f4cb92e3f30b4dd2dd5e3da5360430c008237
7165549aa416a73c62a50b707074b2b7ded2b07454574f60861cd2f0342e4f78
24789278e711f18ef858b819a0accb67384b47145fee30b32181d66ff47aa657
83f0cccb693ac70657bc2bf204974bb3bcbffcd6540477e7a973718754acbe68
823672daeaf24c93263a57598ac4bc999120e367aaa4b54c643e8c8987024b07
9b0d40fb33d55cee534e3a38a1a316276704e9a6df08553fde29e4d4526225d1
fbda6f8cb78098e83e8a360de3c4c77e2998094f920aaba9c7587735cd2f22cb
e17c6b99a8286519242f18de4aabbe470bb8e0931ec7f5c19e1c304df56f2368
70d154e925c4f2e5012d52a0283ea52acefa09d2a8ecc832358868bce8efba7c
492e3575c1605150a3f7d6822960f1a9975151c7b6e928fc07f73493351895b3
5ea783de8482144ddfaf6f881d0835472a603fcd52464da80de0c380fed5cc67
e38eea70c066dadf026e03fe00be35c6310f64aca4b991ed4bc4eb125b4c0a79
b87109b442c0b624c340271988ca36e92157ebe00ace90fa4515b6c649b9ef36
f82cfb4954c124878dfece799bd987ee930148967069b9e6ff5663689e5d186c
26dbdfa146c3dd3ab9c2104fa4e92423c88a0821443aa8008b11008525290207
146118e39b4d7893fdc8c7225f4c97fa3f1cc264122afa3a87d630ef325d3778
28ecba34700bae5038bc2a1c2e0476351d9e73cb623cf58eb35d4c518630ef2a
f8b64bed95d72bb7403e652e2dda6faad38fe8fe4319ae190f0496a1c6806cca
10efc6d15c7e19522b152476c36f9644a599da6786df08fe7981f9eaa0e8611c
1d3773b2c6291663f0ee156b310e2ba3a42ec1fdf11ec8bda99bf88d2316c740
1663a34cab0c691b6ac03b4eb083e8e043427c28a2c0c9afe2b749b8d34c34ad
b130c7fac6bc26dc1b8fa3fe1462e6f344c1bcb311128b7fef549e33bfb5b81a
fc43e9a3003c3d0c44b467bf7df140bd3fab47d4bf85ffa623e6d3b4cff4cd3f
cb4806bb5d4b098f3cc567e9da9952f5f95048b505dd58cf609e2f9d944edb02
f6b959dfba02a986463f09d933d7b3fc7ee6a88a4f515aad8b0ecbf97ac6ed27
2bbcfae1bc994fe5223c239616b2b23a8186a8f4c76c77670fbd4bd65f5eed52
68258c037ce974501e9d4c5cafa853d441e20b4613d932fb941f118ffd512fb3
560ffa1e35f8249d0a8f141a95222394672b524a6d6d924cfc4511b35eda4b5d
0e805183d2990cc5130ec9f6deae9a3eda3632ae2e6a11b35fbb619fed16d0ee
775801160ddc1ae68948c2eb43277bf542e28304ae29f30e5d3aa3f2b83445b0
d883e9bdb962dba6fd1d9ac98c49e358198d4689d4344ef74de18d70f0a0e26c
d5110b932542fc982d4007668feb42c8ebd9b164fc63b71de2cc1967a1b283eb
5146987aa44cd3604f4da0c8d4ad56efa9fb157871f1013b8669e0e9fb79abb7
1f30161f7ed5e4ecf1bae7818ed4c8a345f012eaee24d3338e737ed91b0ae2aa
ceb599efdbd30eb0775354b9f9e9f960979e6bf081f31a128f9eb02cdec0e817
e1dddf1dc6df77d48c4f103d642736cd77c2db09ac21af3c8984b6300674a2ae
abd3442ee0935cfb511469469471f02429f0dcf8105bec744b08a213f434300c
a0f586ce9dce2927bd0ad3c842c439b98d1f5e6c8aa3df39950b1c358c9af731
6ce075019754d92ab88a1a9df0077bad2415f5e7a649792dc05cc9fe8d9ad16d
eeab788aafaf232706a59423d7427936b908601d8a03834baf2a567d161435b5
52e5720471bbd413a3d77a4dd56eb3ae461edb7cc7013d8a5fd540815c9fb3b6
5d3bb3d5a601ef4395b91c142965ab6a4199fb03499757f0f68668650a214c10
1eac3637b3900c5c2f6f554fee41e36898c70c6cd6009619ce188579b08d6dc9
80be12f2656a240f376bb0f2e2871a1bd7c270309c0d9c2ebf067f281168492b
cc7801565761da705cf60027620248e255842a174041c9cc4e1faa072b61059d
e31789ba0c3710083422e5d8ab97d5a38fa273b0d4e611c4417e629c3e671688
02de0fc99b4be7006f4e68fed42b8ca3852d07c38bf1a1b96a5b5a64776384ab
6fd5a394d9447fceb1af6d469f5a32c06a2b40e2406da2b6b0eae8b4e9528324
8b42fc72deb632732286c17218a1c343c2bcf2fc42dc8abe2c250024a183e688
67600d3a48c669e0f598ed95317dd5a2fb3ff4c42019a0f4952c66ebd80faecf
7e36cebac47c2bf13d47bc9efc03fb84e953dd050d05a6b057681d0b7e0883cd
e4a8ea7df485266673f31eb03888c4351943adf37537b3b362a3d16c4c14fbd3
7797a63a93f7ae7ccd11b766a63c991229d539fa82ad3108368cb6d8e1931110
c8cc11e0701e3a70c992ab74a4e8334b91c05d4019de00b26b4d00f4dc785a95
a80803a6ec6480eb4d2b257db355bed7d346472bcff9d49fcb7d00d0839f8f6a
4e038e6255d60ee3e5cd95513e24b8a5c7adbb56b77dd08c0131165d2fc26357
a202af38f951c3f337fab4c7fcff0b3105a79a6799ff7066b5e59d3caa12c0b5
f0ef1be138cf26f1cc879e7ad6772e73dcecbe0d0acc0d497ee654cd6cf858b9
f641f48837f61b054494c361de9f2e1388d05ae4623e944ca603f0ed3dce0bdd
d9675644fcba71a5218d6e1d665b5eb185dc091d4e20e7894e935ab52cb4f554
37984b6187116ebe33dce15360a9172cb4a3f755a0ec445ef335bd3fa097b3b1
6d8438d0d6d74b9f5012aae2ac03aa60d149c194b264ac3b12ba96f806be7c3d
273168063f81683b09a37efe85e40db655d5550e707ea238ed03cd9fd4ea3dff
6333593140c974174c829558916efc2568cabf4efc25ed281e23b5f9b9ca862b
e8fdd5c7e299596e654665a84c7a3a7dd10200b78499f7636347fbbe09804f9e
24e6ed9bd2dee3a3a1350b375c0b2d9e69a12e1056fcc5f0302b5428db9bb952
399d5b5e5a7a41973e1e2baded98ab8dbc7c0a6d9f0f64106bdbbdce75b8fec0
c889c835d5a5d63e9df837ae4d527f84caeb9f92630b8a71b30eac3023dd0fd0
8ce556130e32e9e773298e498ebae3dcba9b94e3673dcefdd622660cec55faf1
cdc3220e7a352ea40fdd4d085c74f0277882454380babca245c13741e63801b5
ca823ecab1b1a94642797a07e15025fd436a72bc6c40056735c60264ca3155dd
bc936d7c070784a30e1b8f22eb8889dbb17846b1eeb0566b08038a7077bdd2b1
f9765ee36bce2f06689be3945a8f78932220b3c3adbbd3faf5b4bbec541650a6
e0d3d48752e24602bf372e718822818bf3ffb976caa33f9684ff248eb0d669ab
9a3e5c2d85f37ee15ccd2b271427eff21d18ce222ff3477c5c223e837498c62f
0fc7255c10543711e6579f391f8aa341a658ca7126aa2239195e42369d2ac8c0
63e1fd8b0f91b6102c6f97f5026ec18b483edf73ddab865f76459f2268f775a4
46dc4d396ce48d2b77f3c4c274d231b028324d9608cadefcad9c4bd0648264f1
cf2a7ee66c5a650101d0b0943b495cd44bf64a9a9b22d19c18e137c15a2fc411
df931690ed4e3dca7b841c7bf41a2f0dce99a059ee3c3c821ebecbf3d51fbdba
c970a4765b92f5a6293dd8fa2cf2b25e0001afbecd291de70e5d9f1511dd6346
9f1567c4749dba82c76c40192af64f0746da17f459cf200674f1164b70868761
08aa87d78e967b973dc20d1a8bc936ba6ee3ae344f9d18b4badfdca809f1bdf2
73682c763ef5b5945c42ab06afed4b33f3ca014bb0d330acfd3548fdeb6bac08
b9870b902dc5018a3dc8e00587db6ca31810d3f837cddbb2ef1c976fbadf144b
db32805ef4cc6f6b1f3141fa313acc5c6658ed248cc9b77053a67b926cd92fb8
7cdbf070ef4bd5a463dcc84e2e6fe78c4f1cce2415e4cbcfe95d5a115801599f
79773a267de8b8b75db241d216a3c80bdfe6122d61a83ede4865d3e6be0dbcfc
ba69be73828cf1292e0ce8747ab06b17d1dcbaf44d2036536c411db0dd2b7a20
4c9557008f7377b324c4b49872566677458f7d87372482c25e672a058f976821
57bb9a5bf95fe43e993f3b3137345c9a7d42528690079e824af45a317f213c32
ac83df6d4e53f991e7c4b4f2951675eb53fc4dfdbc9af4b7c1526345c4ffde6e
6689b473c97fc93afcfbce43463f1ea63705479eedf87f3747950189833a46ef
411f9c68e287501b559d91ff1490b0d77c67bac9131789798510d026b4777ade
eecd205f92159a69ff78bec0c925dd855b3d962304c0089a9deb5315c89c61eb
73c7e8288ba0baa9774b5f4a08a2c8c00d5a6a3bf016630650b949727375f1a8
c891859933377251eed80b737ab9189fa931ca351c8439e496351a11992d8b3a
3ddf6387e4d8cb0547756effd17592bbcdb97e8fcbb0da3d41d6c6a12feb7313
1c530c8331b25749ed4768a496b35faf813edf8e12a81696c045
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F4_0 /YQYTWD+CMMI10 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/gamma/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/pi/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/period/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/A/.notdef/.notdef/.notdef/.notdef/.notdef/G
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /P/.notdef/R/S/.notdef/.notdef/V/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/a/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/s/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font NUMAFF+CMMI7
%!PS-AdobeFont-1.0: CMMI7 003.002
%%Title: CMMI7
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMMI7.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMMI7 known{/CMMI7 findfont dup/UniqueID known{dup
/UniqueID get 5087382 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /NUMAFF+CMMI7 def
/FontBBox {-1 -250 1171 750 }readonly def
/PaintType 0 def
/FontInfo 10 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMMI7.) readonly def
/FullName (CMMI7) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle -14.04 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
/ascent 750 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 107 /k put
dup 116 /t put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3c05ef98f858322dcea45e0874c5
45d25fe192539d9cda4baa46d9c431465e6abf4e4271f89eded7f37be4b31fb4
7934f62d1f46e8671f6290d6fff601d4937bf71c22d60fb800a15796421e3aa7
72c500501d8b10c0093f6467c553250f7c27b2c3d893772614a846374a85bc4e
bec0b0a89c4c161c3956ece25274b962c854e535f418279fe26d8f83e38c5c89
974e9a224b3cbef90a9277af10e0c7cac8dc11c41dc18b814a7682e5f0248674
11453bc81c443407af56dca20efc9fa776eb9a127b6247134248295bd22993a8
90e59bc557eb047f87afca6de68de675a33bc2806aebaafc9c41dd84b41d360f
709c6051ccc6e5eeb3b1f381dc4af41fffca18038106bc8fae33f0409e1eeca4
f248bc301caf6cc4ab0e2055e21c3d53fa6e313af49a09d71f7a55328e21acd7
caaf0ae5ccb91dc701a5ec1136dcef26ed582164945baa7e8bc36793ddb0d2f9
a58a9767eb5afe5464173fb47d2a188942fc6bd3a8c8253e80d143cb6385cc2d
8841a24d4dd8baa438065f8d14b92f393950059d52b71f0b6cf166a3b12df464
5d820e09acfddfad4555c51bfdc45fd1177e66dd1f9deb2afa6af714adf9910d
a0897e60ba286b917340e828089a905948b6e8a9b588be7be9a93ec073d4d8a8
a49f39b3def7cf9751279425c2a45e8c0bcfa9b58927ad12e503719e541509d4
4cf542912585b0078869f1576c15efbd3b2cc6a44c3cc4505f2016d43d0f8a1e
af86cdf99e303969877cc5a9e8c158371f5052a43a27d3c413ec153cdfc28992
3d96bf0e4662f10ee1ac349f089b4ec77b49fb006320565b16caee525c0c3417
598cae49dc8b2bb1147c0ddf202831428b5152266facb8847f64acaa5c9983b5
df7b44b8737a2001a3a20dde63a2090cf54e66bd4ea2f2bc28a482a3cb3908e6
03fc2962577a2273fc5af339afc8379026f75107b6151a2602fee6cf761cf8fc
2f5f9332027bfb1c33da80a9edcbddb78986112e27c360926f3887cd0d83edbf
ff5c293cf1e1128a7caa33f244043a34e256fbb0c37724db719d509f7363b7c2
e9e99d87a79f2545a8ab671c4f7cee7a3272dd1d51d6e4d342c363fa6798d23d
9e92ff1940e35c128e675e20ffce1c4534f300473918e6329ada01df2141d3da
f6b4654996003755017735681ccb2b55604edf1afba9f1903c1e717bd8e4c6f9
80f2a78e81ed2f96881c121504908414954bfbfdeb38c479caead822dac655a1
fe092b9bc795da3aadbd847fa25b143f00fc119c7cc96d3b3cdf4d2fdad66761
91ecef0d6f689c0a993a5776ccb4c9dc22ffacb20f296a98a1d251bce98dfca9
d477b59aa12165b9898b3bb307d84650143648b24d078d6d475a58ff39517602
6471fee737435ba934c89c9e575d22a26293318a9c634efc8a49fd2f252dee9e
1cdf00fb3e0eb3b99b26cbf6b6bcba9c5bcd93fb034ca7f803b459cdc9c021bf
0f4c2ebe0e45e1655fa2439ec87263f34922da2335706c86240ebce4c1872357
fcc31687ebfdf4d7c5aea2562a131a9c5e2d5a48685d90f9fd884dc364cf26b0
77666f83e4b55ab35f7899b64fa2b5d3f8476f5693e12569d7387a609e143cc7
86bc861353e017c7f07b286acf2e4b52598cf5bffc15237586ee95b9c2e394a6
976e52ced5d69488c44c65b678ebbfd5e79ffe0884a110571f1bbd324ec20bdc
b86d16ff207be283593272eacc704653c0af66a70c02f7a2d4280ea7afa83562
34853b32ba7d24f11c1718c2110a0343157116155ed36000d50556b4785f2ddc
8204df97705cc5daa5ff8d8efa85d0f06636c8d56bb8040fd345b18d57e1daeb
02a7ba31ce78ecf46ef96e99f10358c7a36a89113fb06342dbace1a098f5baef
0318f0344e778e18bce13774342d78944f4b7c2e1ac24a489725cd99362e6af7
85486904aafdf0a13e6c67ee26fed977b0a6ef8885d47c863543571b29a28c97
82a581faf288cdd73699767df414a6343242883e0e02c5a8d2ccf371ac25f17e
e33cadad78cd3460ca416fc3cea16cafbf9552d84e06d79d1719e8b5c348fd2b
16c1252da6938697bbf6569dd2720e8ba9a1572a64046ea9749cd5ade1e61a18
446a8531e01d039bbdeb72fe18dba83d6e0db1ad996ed02e11a94dbabc010895
af248e4a5399a9904e68a2e1fcaf0dc664d9c79a0297f6c858432c892f24138f
1f1ff06b18bd0ccf394635cec4251b41e5c0e082de87bf7f37a7bac9e0d4b7b1
700ee540a1e1ab8774ff0b2bd48ea78e89ab7ebff30ee35e340dbb2c1798ce22
8423986e21b5bdf5a5cb547149be43242ab1380e37fd72f81fcbb91ab7163618
8556a440b87d4dfc6d303ceb1dea4f204b65e527a769ad7d8bef1a4a1d33504f
964f9e42336f159dc6ea576271ff2b350e78dd02795516d9733e4114df4f2e02
62b6b8894221644d15c3bd4b4bd703a121b452d6f95ca2102df639eb169b3b1d
85a901c7510a0f77b982884c256aaf3ce16603d26d741a2c98d73b1cf0428250
3dcaa647ccd4344130de118933495a99551303d5f83fec47dc64177603da28c0
1c62d4728780b2fab45e8d138a39f8b865824dec298823fee08fad12c2e4d4f2
ea2bab6d73e63aaae68402309a55551703bdc7851c2eb9928a7cdb415eba6e16
8501356eb391cbc473844861df59c6900a7830e93c04cf4ba4d285c5ec264b00
6e13cb5fb7cafdb0a9da8ee4bc17821dc2b73dedc46d1f4ed953ad073ab85705
3cc3d43a8a0f3a6ffa923106388ad64d98a0fb692742f533bd3674bba18bd360
e0b7fc6b2a3f5e53623db8029216a2e2a5e8111ba5bbfe6b2c2938a2121fd3c7
cad20ce7b4775f43b705194e8f3ad2e6597e89256420002742f60ff61086dae5
9c1331b38336eff3aef839cc52b0d33f9cecd57671750b147c41b7d7b97abac7
4ee644b01435151b5e14a8fbf6cd49b9820247a09ae7da65c91808c3b4e08360
96afd798cf189dc669ff8a823aa51df4bddb7a36038a35bf94e68ca908cdaad0
b73cf3026b0d9fd7520fc8f03aedbb93e8614a6a3db785ce9dd843116dd11b64
9bcc485008d4b66d6383a656f7fd51e3f1823b6901aa69682cc47210749cbcdb
df3c543829e9cd96ab01aff6733ea0ce93c1f6a87e631c8be4eb305aecd823bb
62998bfa70b172196733846a1e4e971e2781143cbf3b96549ddae2c4931b839e
2dd158a674fd7fd646218c85be00da0a3f09cba25b321fc67d2b2d500b1ffbf5
e9ec4cdb3946e61ec603e26656dd8ef7a4be34c6c9f23420587fbf90b029b3d0
f12b07672d04cbd918cbd9b12a896de17d2892550e9006becf59c491555ed2c9
3e0a2bc0a54a1e46649318cf25beb38aab1dcce73a3dc8e867454d8be400b175
ff5192705681167026375b3971db11516f49eefdfcb55696048f4d325d61c48f
f920c128001fadfce180fd7cb166d92fe2468f72aaf908940f525676fc915ef4
f304f0ae0901f6cc7cc4a92d9470d87847edfdef03ab0f8d9d077f3f2707e78b
67bf7ad8166cb2a89387f8f0ea2ca0e51bceb323b8a69ab941b64346ad999659
6d9e855e0bec408c2e13a6d873d6ba90ef3e1b66215d1cd8d74a11a0d2d34310
47fdb07518bae9d551168ed279438fbcae5773d916e30dc3b0e22689b2814954
1b1146cd804aedbe65cbf30fe88d262db2652456a0cf6b2517b209c4dc16ed96
766c23f62736f19b0b8bb338f8938b0d48dfbe4182d8379ba35db069d7881133
655908da78cbcce4e5882f7919665df00aea3ef801715ee56092f281fab2c200
11e67e27b39d7d0360f333fe04c1e9f2d428e6e431abd6db1f7ec2e97ad4526a
4177f875ae613823744ecab071a1ef05d10ea782a4241001de95831491534f9c
d04f15a2ea4091adbf8bb5bb1be479111d7b31ed46c5abcc0796c383298a5e46
4b81807d4a2ef8d0401dca347a0fdfda31be94e3443324026b192c8130f0a615
c19bb54961d63804a1ab198af9af1c1c91867050dd5172b543c269ac99c8d86b
5d71427e1f26a5831488aefd9e945cb75054575c7d27ba350ec6ea1020c7da43
9f7a9d8f653cef28b9dd15c0051c736ba2a4e86ff107b4392184f8d83f147884
d197e245b594b510ad5bbf01c3e2929ef6b84a3e26e022894282f1091853639a
d78af4191eca7d7f354481e56d445596bc68d4e94b7f314d296bc6f0d8082950
f608252d2f6c117c74eb05b898fe63bdfb177f93e1540c5f68c0df68b101f18d
6bf29787bfbcdc911db687c943b5b16c20f4e0616904266b2730bdef98b597ec
0c8fefb07659886f6b3926cad833f6b314ae3532d858c73872fccd7fe95d36e7
312a4517029603a387586b840c91dbc76406602d7357e3b49160e9045cd28b27
c6fee9cbedbd21e246b4d5d19966b13842b8d666d985c4dca7282900b3af9922
518de02562d14018c5712b925e50b73641d0e4751faac47de00484503a472804
056a83da482a4a7d61226052dad45f9fb5740ec9c5ba4700f41c9ca608eb7b4d
df381f442ab2522cf8e4252dabfeae1152d6ded67f5fcfa2507ac551cc6be5df
047106d44d2956743820be5ee716eaf70db25c6c4b8f9f8d02ad827437235de4
eba2aa12784e95415644506a748751b541b08f1154d938d461f0889ace080daa
421845d6b985e55f63ae05528e109b32764e12c66c46de9b551f27b8e4797ce6
ca4500a3f613d9331bfc1db159466fa060c25d70730a8a0d899525bcf4c9e57a
db440dbe360187a4d3acc998ece0945a02c05c7bb2baeb442d704fc93c8ed1ba
8585dd7d99d04b1cffc85126550ca4e4c8c816062f0cb9d53b79a495a3fdc4d1
651a7a464c98792594f4e78c4ceff967ae4eda9dbba517fb6e05181504a6bd4b
18f623eabeabf9f4d65fbf3a13880e475eb12905e253111238c8bcca5a23a9b4
416829b1ea3c1aae5cd6178b19e65ca32692da965376baf6fe251b4b9751ea8a
e22720e6a37fb107fd1a34398d24bdd58d15480844c9305979682928cae73bf1
5b3b96a898b9b0d1fcd411e7792c45e0f1f9e0d556fbc5d0c84a7f890ecdf7c5
f307fae44f2ddc2b69266c06741e69748f24d8b2cefe85091b18a116d42c887d
e6f1b23ce0fa5bcfe424791dc79fdaa92b8b292892057871304bf5e481e9c4fd
dcd1d7bd74ad89a0749b9390a6bc22102f74842f4d8193add612cb77bbdaf5f9
0a65c91d372b64041c571f7ea2f5622836cfc7883fd9635fce6aa2fa0a5ddbbd
56d5683d2da28228fc5fc75eaa8c1f3a607bcd3fa6ff42bf55fb07d70726a1ba
0106e5dcf4f6d4fe09d93948c4715532f2f92de900319763a680bc64f044b60b
a41943e5c052f835764be645fa6956de21fab8e7f9b9b4b13b71950f921e0f08
e67490fc4f2537577a93f397ed6a7eb1c2ef55675971bc84e5ede78f8e53c11c
96b4dff057cd143c66d5e7694fbccced3ea5584b8e4cef3222c53e39af24899d
1d3addf0ad3be37f06992060906b0a45350d46b0c1011c18426a6c9b117c4481
d7fa3caa75b4be4bda1bef19ec223dfc0138382b2e3317fdbbba5ed8112eeb34
d0f717609c19e694437a927ed189e2061a8ad4f8acdb33c2037b24c91355ba7e
fba89969e5d52e3423cd86efc7ceb6263d1a6d9009cf54b2f7db2c05e7f08cd1
3dcdc2a8ab9a12439d165ea2e26a0dfbe6e046e267b2f1b87b59caf96cb565d6
762f77df70c5867bf5f0ceeb60cfbb7dbb9b983433b51f46c1b2c33328d4042c
63f3931b4922ceab3f9fa33d61f040dc86b464c6ca451c7d9b8d5089512a522a
24d7d463acfcc1dad90d11c24987d80c2d90c49b80edf350d1cc22057422c13c
d79f954ab97995e7c62e5e4d980af960dbaff4d4408fde2b6962a4b31a71bb8b
666b79744caeec627358b10fa130855fa44815f1c82b8e1e90180c99a8b70fc7
25154c8bde7cfa1e716c77a59f86ff3b16f2752d2c25cdd09f05166c1b22516f
29812cb4f6c021acaca5eea3009cdb09110cfd489a8ecbb9f3513aa3c99e1d14
0ce830d6eeb744de31e2e24b3ac5072b3dfc28f4d888ea8458f7100dabb4b133
e3d82d5c6935226ca6b0c461d7a58c69277a4dc29b3fed08f96bc55c30734d12
7c1d6e778bd9cbd4453f3ff8b5387b8f9b2add85c38a580db29da6149794e61a
31822cdf4ac2f2a9884ffa52b4acf38db7a5bcac30a611d03af21c0e18f23a0e
bea02060a4e9066a015633e3a1b6596df1237523b98a4c60dcb74f01a741aa3e
f4653a0a1dcd416bff4eca3417edb6a94ecd16f018ba6b634f71f88c228a8238
1ba7262949daea924092aca08ca50a6d283da85b343471b77f715a1e75cae530
505f2f91d9a7eb3fda227593b9ed85b6bda43b408cb420afced5d8e69f8a9689
226236284e8eff7d64562669f61be11a252a2535ab14a32c2ee5e77f8ba8cb56
926f66f685632e3ba4c1d0eeb88a0b1c61f92f8baf7025c8e77f6ca8a0ffdb09
2a7522184dcc68f936982ce4fca61b891436c5dea5513e6a66f45211a7f51a54
c1ee4ce7edc5a7da0eb413d47b08730e1fc502a76a8f0028c1e6a9ab9317b632
25e9ef30c5822e1991606fb37b4e820429f61965f0756713b6e8168f934227e2
17fa622184293c9684872140c82a3920faa4d92c970a0f2d35fa3c07af7b847a
72c095e75f18842826c868018077cd31053ce16741dceec7adc9db38bb5f5637
93ac16ca652aea23f4f1f750f070ad622d48935f8c8178f2cbb4befe14388288
f02c239b5cf247aeccd831350a87e5dc3d232d0ee7ae82c32932d947c405e9b8
0d5c6e314483a3f7cd3c5fdb7a1a8863b773e28f87959afe29229dd1a6b13b3b
15e5f613937c33feaa50842e6a80b4e6f7317beefc499e2011f68e70231c930f
633e6950db4f04594c96115e70b265aea4ac06e74278d2b440792c34ce00232a
2abc50593209aae29d99aec880cef679e267d8543eabf4f824f85bad96125893
7b4431e97415f03f4bae76fd20b1cb7bfea2d7bad26ade9c99fee9158722c934
257b43eb7b02f367c5aa5018b969d63b1254a14d225f3c022e484e554698d893
87f1cf88c4c48895dc304e994c2b2f6cb912e351cbecad71be5814d70ab2ef9b
77f4d1cd5e57eb77c4fcf0aa51445d189bc37e40387e289422fe5ad2fd559d15
35c19a4b2201d2354454fef30a699798751a7221866c462c6af03caf7f581851
667843e3bc95583a0bf39c25d36c8095c9bb71cbb8d9fed1ec6ea110930a1bea
beb8bf61f23c64bfc45ecfec712407190fbab868195bc58e989837957c08fa00
16b88e2559a2e8d980e1a5eb790cf34ffcc780561302cef28262d2ab31edd903
5d397da3fb8705f17f0b8632f616d4ab90544113ada3a5bccecaf90c1e9f046e
7a3f4c9607513e860c5a8388c0534de9e2bf61eef8f938c51cc5226b9967434c
d48f0ad3d8fb22a8cf93a08f1ecf6c14239ceaa20739169342804d6abd5881c0
7fea33d2addab0c8f6eb6e4519ba7f6054eb73a85bb5b613cdda9fd01c08b24e
afdfd597656ae22e44e8cb1275a70d0b324f5184ce61199ff46a6353986423a8
b4f96f5b5ded22c1f0eb7d92b581c391053aeb85ef2aed1614b579300debbf7d
ee98ebed06fea9445d2c324f51bce3e0975e453aed4d6d5853371cc700005526
ae1c13e580a79b03ec36b568e4f8c266839089f9bd1a406dc5b375655bb0c30e
89317f2e58af67e58840f0a0e7e8a86b5148d24e1356bcec51fabf8c6154ca62
3801e54db8ad4a7d701d707fc710bbeb2b2b1ca51769e953e4bf536afa4039d6
995cdd6714f337db974a88faef3ed6179a3e1b02865a0dfbcb61449098efd8b1
b5d48e407ad8049b71d432d0d8f9b18c96bfd497397b56f76bc132602df6cab3
70c77457c8de596178f69d96706cb5dfcf2450270bb75f9d66221d0aced2f5f0
43b906d1ad16258593b23dfcb4fecf198aa5c28d09c284e096da4aff7153a7b5
d44489ca71b28d8d4ec078b97c338d4eb1970d1a0c716b559a93f8a917dda7f6
de559e13d64772a5bf9d048b00b3cabed2babcd2cc5ee38dee98b10eb1504d69
0003132a179675ca52846bdd495d2231e021aed9f32f2a5ab76537553945afbf
576377a480d93413e1449cb7ebe273d1dec1f68249ce50ff9def3b4a9180ae88
800505af000ffe34ab15083c9513250218e836c454551bad4e272cfa608ea0e9
439b027d24ebb6d33c520c5b6b4a2daa062a95ce9990756911072f7a212fe739
31e35931ea899678040d86a819ea84b9675005084e068623378c111df2dae306
369631afcc9e1030ab1b8a6bbaede3794fd1e1e6feb5753cac6bdb9abbfd3a05
75b406ae1f1e2412c3182f2d1a5db0f1a91f61d44e38f34cd517900fa5f594a9
7a1555d97bf54e8135dff430a933e00747687e36b7b7f0b61c238eb9df7fc488
4a472a03579e5fe2c00c528f2d9012dcbe7ec9ac3175a2de1eca9852644a2776
97f4a7c3520f14ff2ca0b81acbda63beb5de928a515d5a421d065bbc57de78ed
93e3373ab0c627c6a2de800cb6b45b92df20e65788a08b9745f8ad7324c3d20c
79013fa3d674a69c0f728ec98df2ce6cf3ca942aaff8fcfea6720ac2a057c0cc
90e46cba8d81195f9685af4a50a97381ecd49097de783ce665628dc4e287dbc1
018f243a52b3bba41c5fdeb168bbf207162a05387b3d4a8982ec75442fad86fe
1434f0275b8db6d3d348ab8ecdcb84be0791d081f265a9efda468970aa32854a
b5040af8fe7f1e3bee00260b5f10f1e04cc02da1f48073700756b46ce2143191
2b53fb0d085964527bb90cc9748001d04baaad1c119af1a8fe61e20ac9ca1912
03417ea43339e613d9
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F5_0 /NUMAFF+CMMI7 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/k/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/t/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font SOSTRQ+CMR10
%!PS-AdobeFont-1.0: CMR10 003.002
%%Title: CMR10
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMR10.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMR10 known{/CMR10 findfont dup/UniqueID known{dup
/UniqueID get 5000793 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /SOSTRQ+CMR10 def
/FontBBox {-40 -250 1009 750 }readonly def
/PaintType 0 def
/FontInfo 9 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMR10.) readonly def
/FullName (CMR10) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle 0 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 91 /bracketleft put
dup 93 /bracketright put
dup 61 /equal put
dup 40 /parenleft put
dup 41 /parenright put
dup 43 /plus put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3dd325e55798292d7bd972bd75fa
0e079529af9c82df72f64195c9c210dce34528f540da1ffd7bebb9b40787ba93
51bbfb7cfc5f9152d1e5bb0ad8d016c6cfa4eb41b3c51d091c2d5440e67cfd71
7c56816b03b901bf4a25a07175380e50a213f877c44778b3c5aadbcc86d6e551
e6af364b0bfcaad22d8d558c5c81a7d425a1629dd5182206742d1d082a12f078
0fd4f5f6d3129fcfff1f4a912b0a7dec8d33a57b5ae0328ef9d57addac543273
c01924195a181d03f512ccd1267b42e8964a17d77ba8a5dcc6d878b93ca51f9f
0d2c97dc2d102ee8329baf69528b6eb7c3b176ccd9be31e4a0952084271bc613
e493b1a9b7145f72224f15afbb5f8b1374b1336b651de8be6642ddbcf656c166
6a971cda39d2b3ff20d40d5968eb80b8c17bfbb471ddc9cac62df78697baf8c9
b7cae3c17d57a73fc53f1c6777312a45685b8adcdb3a9b1d9705aa74cd02c057
654914102cda769538fc0561853c7b82f142fa1a31e2a430305a3805c301cc1c
ee35a07cf18e7dadb5f04ebee0d411d76c77125d83ff83364eff62bf97f0f0a4
19683345609c8628a19b45c189a1de8f27513bb265b5d483aa2ff0e0ad162e44
a9791f4c92e235d8f1c724a5344947c3e5d7aec98a5c82796af939a32eee56ad
55bb9035a35121e4ec8b2dcde8b581c8428385c439f664e8e2f6abab425e15e9
6f56f9f0ad778842c98ee1543784a189be52809fc0734f9947418b02a6f7e3d5
c3096223ed544276216db78f0f57543dfae3cdc0a6fc772caa49442527a5d94d
c54be93c877cd95dd844a5c319b080401689f5b78032b2bd4ff828000c9c10dd
8e259ce6db03235fbdc9b756f1fe1a421b5354f8a2237ae000c3d7d2cde321cb
d1e3247b6cad5ca734c4b8203b358c99036c912621d7e3809af3df3d288c8afe
668ab8de557741b4da1cb19bd4c665dfecc8cc04422307bd3330143eceec4820
a4a9279cde4ca52b14ffd6939e6ae27a9d40fa1f8fb83dae735cb2de14f53c85
ab3d5cc0590124df443f8855ea09d0e6fc36959fd27847a1516ec7ab1b9a8a19
e469af25d6949e21d7d10a4c320017b15b9e9a11f4e3a57f29218c6685588208
63e8118b0800e33cd52714c8b28f96f15213503345a121842d3ab1112711e0fe
d0410e4a0faf2e05d9c4b2434ace004a74aa0026c37b37069036b10a238156d0
c3d0c0ebd5d648d51b93f38b2fa9ca0e46d76777224635948f77f15388247caf
ff816f513ccee7ce970b0bd1607eb63c9d1e3130a97c0899ff3cbbe96defb4b7
f9d89cdec968f0dea084dfade98008b5b5b0b09b3fc919603ff33796eb160b5f
cca0055b95bef33878503c3431d51df33d74cff84800da0f0d3b3699b9b87d72
4b7531e933fb9a55430005699a16b44874adb2d1d37df679181ed6fe7e631e25
5cdf71ef805cbabae6344f3476215b9b5ff749baa2b0efb3affc15c6e6638b1a
30df1dabf24d4af94d9f5930accc8f767b36df1894d65cf8c32002729f71c99a
2233193df703949d54d2594b2edc4b18eac929c12c1747ca4b7b6188435a4247
9ebd0a1e1d79db280e8a4b2786c3324f30d35697ae36495024246cfbe9faacb8
2d9317e05bc018ebd465cdc98bf8c71a08194bccd7263225679462af7a87f74a
cc19992c756f7e4dac32c4187ade759299a087d4362a9abb2aa60dc5c20dabd1
ff39bfcea8df3fc4a34b9416632918cbcff7e15cf0679f74ad263fa9e38ecfc4
f4fb6e0654eb77bd93e6bc24a0644e5c43b89ba4ceda4ff6d6cf40a55732781f
e83871214c64d2aee31b6feb7ee431562f8cc8423d40b1f4faed213092c159a1
6f7af924edf9d0f7c78025c4adbfd1c91577e1dee1325d6faac3df20ae5ffd3f
4968cb0f75e8a1426dee4606173ab5310e08d8966408a9c87936f782c0dade20
1d460da884184c6e3553f27726a92debd3b0af9e477af8a839ea183dc82792e4
28ccfdbc49fc684efab4d67be44f12200e9831034c7663d56d150569b5a6c026
c8224decea6dc440b757d586ad18a4ad6ddc622530d998052afa609aeb07c4a1
93df932f66f5c39d6cbd25504532a13a1e56412953424c2fe63caa16ee3513aa
439e41a3dff79d6c3bae7bcbc00b2823bad858056e46069222088b0098008438
7b52d86f9211c1c4541728e45f57f0026241fe7f4b7c6f4d0b5f13d6d3975711
dffe1c91bd0d79e44de8ff3680aba0b15ebdf761749e1f08404f31eba12f9d00
46f11f94b633791e2399e3630f4d4dd7d047c55afddd5b036dacffba7acf8c46
7f0609126caaf9ab22c24a3eae6504d856428f57421c7de756299004dc53c8db
69192ca1ef81dea7ef521216b816a5bdbb468dc703aabd509d2ee8bd4c04d180
78f804a6185f5bce5856881117c7f3f451a0af0d5450fff57683a0f90a65ca2c
9270feda1a83727f6893fab8937516f190848c602b6c7b1a08f76551f7d6905f
40661736331a48df506176d17a1955cd155fb09fcd14c65aab311e2aaae4c78d
12af8f4d2bc7627080863b7bddaacc0981ad513316e856563bd8a1bccd88d30e
0d12ae4f2e4f9ee0692cbc3838abd61e83ecc38685679f3d5c3de0402246e0fa
4b46f854a162fb9891be56818e6c286c67aec19dda62d2ad8ddd21b8e8aad596
d5cb5ce1fdf96134513117b0cc7e20ab39e27156a5b8a7cca52092735e6beda2
73648e9b6e0e7a91c10807ada3e7a43ad61c4c9e7a195d8e11f0aa720b8aa5a2
aa83764e44be8b4d47373924494c69fe269341d8671be16e6c367901874a098f
464fb5f23c4b09e5eb50cda44f8e414118ca7686937fded26ca226e7b5f859e5
d7b427d9ce0057dad0e58326c0a230814b20fe19159a2f690969d9d27509629e
1ac2430a38c7c47a4148a5d59f33010a792ef25ba078b9e2dd74314175adaa9d
0c7041cf2e5b34a353d8326277942b632074a9a4ee4e651a18681c44ccb2dd0b
c52299211e7ee4ab3b2b37705ca47778191259e2470a5edd3545aecddce89315
121c9f5fdcb99647b5f7e1f0e980281e410c6cb713d1ee3160dc38752ef3752b
eee3d922faf33e3bf02c7f7ac9b4d1250a6fbbafdfa07803c83098738211d6c8
191257314678cfeed4e897df2067fe6d918db5785679f5b5da11d19d225d237a
7e1897a77076f2c10d9d1d869199f6d8c5a82e7242398924156eb85943ad4331
fac474aa644023f7a83800d06b4e87d48b4bb001a0d33ba3c0ead4936c8146fa
28060bd88c4ef38aa6013be0e1a564feacc2fbed0192ad10fcdf2abc8a3cc6a6
a195e3c5138413aa0373c0a6393cb5478f0d4345608556e9a268e0bdc9c42515
5193ce46a56f50bdc4e2d111837f24aa90bd22d13333bcf75039d739ec5a8d73
3987012760e3ad1e0dec72da57f93a4e94a5ecc873d3f5c794b71f400666830c
9c5e1d57dd852632347712a96c7a0be624d43257ef13b277dd85c6ec4f3962ff
a3e5224fa69f13cacd57c32a46125ddd2fa66079aa8c51b10988c9945c5195c2
1b462aaadc695416f18de85e4e20f6645fa34d6083a486532554b34eba4b378f
af082b5299d6ec5b72a59bfcc859f5c513ed5971657dbcb1d81c0ca58bf7d859
8750faf40ace46015545a2ecf3fe8cf0d34b83c0d50f488c27b2b53e015a5140
ce0f49d9e07425a3e4ff969cc05ba82937c426befca068ce6e9d0cb119e95927
d4db61c2b654c3f12758727fd4df992f6e5f6e95034a4ca1160b082896400ab2
e7a0cbd09a0aadb54e1d7b4b46b5dfdbf05e6b9b62dec26eea7e16ed604cafa3
5d08db61a455a101b9c57bfc881276e2ef4cdfdcbae6a23493f43198247f1372
6d41ffee739514c2c6f3f26e5adf032a99bb3da9f7ca73f5f06f9b1462407b91
79d60b082143431f8b7b1763082e577f5ab6ecef1ee630176e0be06270856773
509864242dd15cf6afced49b264c3c70bf0412b80f6c130c7cb97e9bb438e8fa
2ec9c496b62b66cec77a79a876831fe15fb2427aaeca879f86f4323f76d4bc08
0602eaf3bcf5d787c3580161a3213819d5a46d0a96db87186777d921070a08f8
37e54609594079535d7ef1859f0299adf96c6f42d6e9ac93091f969d762130f9
e8b78a4694820cdddffaeea945df615b888266f8507834804885a0157cea0757
fcb43bdb471ed614105913223342f435d9f3fce6f8e1485c22d3ab5b06f83196
ce99ed63354ef839aa703e32374abb42fdf3b5732f03ee8ab66728f4a9781551
2c0e743e5baee238cd934773c5b8813a1f5224395d36142688fa6d79ae2969b5
198a76c9e96ac2f657a88b4cc452425e1d5242616cbfeb78b35fa0d7599d3ab2
354da7af04dfe6eedb14ef8a07138ebbad0fb51b7fa8fb2f6aa485e0c5d9a121
7dde6094eeeb4426571c80c8aae4d65158b9240648dfa7e70fcc7449a4adbc09
7fc8d52ed9591cf140d86e15ab7296105ff4ec6edc81c2080dbe4ffce374414e
052d4c0d6e968b973f055fde165e5f85db671492b57e9e16c68f3b8d601eb0d0
eda84b4287def03665c4b6c1dc1faf91b80a3e94e86cbf517091861aaba27fd3
29c086b69df9b5a5f22f8d3b075319270c5eb9f53ae474044ab16a40ea1478ab
b38345283047ca3bceba15db5171028ea9c7946b5427b9f09e103b9e3c90711b
6ed8e47581746c4c43319358c42035cd1a970a7191d7c471d2a5813fe48bd07a
3143532bc01ca35031c37e1e65c9025332cd0b33ab4a964ddaca84956c28f1d3
b524081eba65c951e52f6d704e354b370157fd658a7c29c3dbd8de618a4896ad
e05ab9d3af34758d557dbfc5c4e7c3f4a806145520d121cb965995ecea00f921
d4014908d459e5a8d39f194b25e863a545afb8ec1efb9b3d42d9cc495d1b8053
0631f72023f3d3ba11680ecc5b51864c68aa592de5827e5372fe796135204d50
5947a9d5d03b1e39048d1c5d04a9d1175900168b8540358092dddfd1281a0af8
9c913e0b9dc383b7c944486a87a210e3731572158278dc960ae62ec23edad0d6
afafa1cf6b97aeda6cc43b2696af233ce7da9ab0f265902966d1e4467a9b60b7
c7b73fa2e349630040534826963cff05bc92ee0465766e003813819d46821c5c
e356b1aa33c5f361ad41217979bce33af1d32b149e6321a378f005968262cf4d
fed689e12f667d33df969bebcba6c7e32247a99611ade727664d73d107d41f58
5755fd7dfcf6b5b7b859c4b58d5e0b80d4d7256acdc72148beef8b4f48ff08c9
cd8e1f5ff9b68b3be887b2cef27f91e24ab876a10eb2815ddc230a24d907aa0f
db2743683f8135993c845318fd1dbbedcbb0c1f14093ad189d099a61acb4802d
1499417f638a86e96c6f5701b44d28f28f067200b7a723db60d7d06e597b6adb
60337c6c02761dae60ba27496ca0fd7fe0b121e5b4fca1f5d350c2caec7b94a2
0645af98ef3dce7061e85e0b81d868eb4f6b03609db7ee9be370f8fa0cad3875
79dc2472f296ddf395750a667d6371c32b35c1797e21fddd5dd59dfa1bf8c0ec
0e552cad01be74a029e6693a48f2a0be4f85c4db28ae5f654f81e91d4656befe
71d006163eac75e8e0c42d473a88e1f1c47a839e859b485a5c258f55ed76d8c0
001e0dd07ae35e18e0cb428d7925804e54e2b8b6333d18ae58ebe03fbc6d144a
92f8162dd33384f71d69e3d74840dc908166cf83fd6bb8522eeb9bf5fd762780
c76d2e1227cd53e3c244bbccd96c79fc1f18379316a20c59f5d643b3adc56de9
b55eb6af4775355f479b07f8b5d931a6fb0f742f8cd40bfee08dcce2f00ae034
89b131ad6e885ffb443e7d70062be666aa673968241dfaa8c5015d40ef4df960
d85ed2b9474bf63b35ab06a477c7ebbb04e4497271ef41a833664182df591169
75ac80c2dde4c3f2bdd1efecd212597210e91d44f5f63a8f8dda641e0752a503
dd20934174110ceb2daa902c1429e2ba61aaa4c9ba68e2cf395bd4a775ff0853
e718394b92198411c4544ba9615824e47767c993b64f835be202788b1b71c783
a37904492896ffbc6a10354ca7aa49c063b57d7c681ec024917a44e21355cfc2
9077bb598d2bbdfdac5a3aceefe7c4cfa4c59c31bff2b56c7fd965c01bc70160
75f840021a7c04acec1f15d6dc88e8b49ac65eda361bee2f9e79d1fb6061f0a1
12a6c80d8a5bafce8a1060d2becc459ea3c2771ac105ec611e1b0ca17ae669f2
4c618417127d6acab0e7c940fba38ae57dc57f780fe6ef57b6050799e56e8773
8e98306e2a0e7b0eaf6c3f5aa97af38b95ca128b3eb8e738ed1f702d4cd126c8
a3fb03ef4b603e2060b4a825c26096a2eeddbfc973aa3fba76cbbbc65e5cfc89
2a9215d6fd51cae1a84e6266852bdbbcbede849e6f22098dd9a75509bc7ad1f3
67ea67cd61e48e9075b446a0d1993cc31358fa79ddb8aaacd002fa2abc02c867
f6ff343f58325dc29034a8489acda29bd7f29a5ec1d0714c656fb29c9855edf3
7e0cf7a59292d0373eec29c6a4f399486e909e02baa8ad413722e97b4486523c
2f3274fd4dc5c7f4f973e5a680fb6b394958f49266a3a99cd103e2ffcffdfb2b
13d9a65845eca79610c82eeae121c0d0c3222a4adb53370ec0da591eaf081ce8
05ef6adb0d1d26d2d941e84a0c2babe688bfb9bb0812da123df5964ea1e52436
76b2531a5459118923db18ae4c97ff34cea7eee73f9b00cf27f6ecf7c3f97f46
176456474cd62c2be7167315ac47fea4e05e2fb8a971b4c304c9f601688cc50f
acf9f95a1eac7a8444a974400c33f765129a9b9fe84dd8403e6a293c576860e4
4dbc883effd7a2c9ff7ee165e0ed56444ad57c97baba580f7dd1a743728ac817
c654c841c8e80b6618fd0298a39294507d3b058a22d3bc4bf6d323ce9154a0b7
0e46f7fa5ce71afdf75ed493031d1a030b3b9909c07cea5220445cc4820d4875
d436ff51c5fdd098279d5133c8623b7823b88e1f33f31f53cc3aaa6a6211eddb
25b8744a91072f3ecaa14fffee9c1d7256de81c219785db0b906bc3e29e2ef9f
c1b55d806c9df903356fbe105be7a1d0463b102c4e26a8271369a98a5cb14e51
c149f248d4cdf4d01fc03f543aed40d846ef17e74eff0b075358c1dd30b13cac
29bb68e057d60681bd3466b94644b7688fdb2ed8b35402295e5305d12d1e856e
777dfd2c0b885a4eb84515d04301f4aff70b590b8d520565b57ac2d4f6f033bc
d25c0ab6d874edfefe59e135608f17467e5f9b78c18d8303559e7c8b275892b5
c7878447400f55d61036490b5c1f9984e7dcf63efc3ac9565ffb02c93ed5a639
2a49307d16d3b55c227bd81508ef3355da7ac6f1c975e4469c6603ccd9a485f5
50dfa8ca29459088380f82fc55a59cfa7729aef067138acb1571d43ae0646a23
a5b9afdc1588680771c70ba59cbc736f0d2db940920a4b0347378fe322ad7c51
d08702e6aafae5205af27a737c85827da3c44cd5b453138aa53a8066aad56dbc
a7c24133ef8fd6f0530b32c43d1991d65bb364b7d893fc4a9c5cdcb3161ead1c
f21663ecda1880fcf90f7c06cb74be6a31d1c69b41e772fe8a15aec0d1aefe19
cc4a76c22c4b1f7c0109f2b485cf9556de90909c0a98fc9b5184b45bdcde3c55
c1583a1c0482dadb3f632bf625e0b109ed4ebbdc4253353986f883c1b3018daa
9e22c3d6c49cb367e854e9bcdde45e62a957c50806db28b22a24208c7706acf8
e829158a8c93e3855e144e2172adc3597aa53ca586261772973b416449431b60
2f88817d0a2d6a2001367a5ccb6cf20fccfd8a9c4b341a2acd814b2d19d7dd57
a553e5508bcdae41aa472783c416c4dcfa17b3d0d2cc45ef32d8d0485037c117
af1eed59e457c92db246ccad5ebb8742bc3677e06dc5a2f70fa14529be16f9e7
f1473584bae8060daed28cde641a2cfa0bcc95e3fea848f2ba7f649af87aa556
d2ed84e4723b3bab884bb606362c818c8785ed46b2205d9b4a293247679e0464
f79d51584476fd528b2fc34ab914c268c8874e34f030fc7dc868912c1f50ff90
78706e7e8d5caa745893c2999a1018ab141633393ac8d20f07388d9a2a7686ca
70dd4c25932c1442e55c975cf75029c56e85cd29498e70f14e3a8a481a8c5879
78fbe78d243c0586b1ee0c63104adf0ffe5f28e769e3a2c92caa13bf26951435
9a039f163b1cc501361ffc34f9a2cc53c085655bf5bc96a18187b7d8f4b141b7
5e4fa3fbe4308ed4445d47e654848f15976adbd981ec7106ed62368b68fed017
436495d538b9da1d69257d416760308bd22fbf5a6dbe01a5aa95767bb7e2ed03
06fe2bfd782d70285c1f860c6cfdebc0b20d672b8a6d9274f1411c0cdc5e3e81
8b09d1e3db0fe941a3454b53192f8c887afd8fff041e98e54b63c50a4fde2ca8
34be95657cd37b8b47bbcaf8237f5276f0e0a9004bce1afd79dd7b204b31e81d
45fa9f05d6fd56cb560477af62b41ce6fb0115d9e736adabc2aace1bd63d85bb
ba79651fe79fc065ecdc9117fcc6f7a000751145d83e4d080e253b2c889a3196
1e577d770b7e6857b90cab97a6985fe80e46cce2d1ee39516379c61cbcae4500
05b8157e00f4d966ae8d04e1137a5ca961923a0e613cffd4326575676712b053
529f31d845dc9d92283d461a993d8ea3833be27127295e313ec775360a47c130
ffd1fbf2ffa69cff2b42b0b82b9be6b89e62a5714759c008f0691674e24c7801
52495076aed51fbd8db768cec4d310d4a5bad2cf8b5e9ebd3a6e77e5f29cd570
35bfd03e5ed8895200a5dee47df034fcb8bf8cf299e1f9de618c1767fc6c1d7d
d75e9928a9743783041361ddd40d26f3bdb61d29b15a53ab8891041aa094be38
13ff6e7d4066303bad14622edba3454cec161a9b37862505b707b99b0f3343aa
1a2cf240e437b9d5ef5b490b5b31731349ac04eec558da3cc6fc7f5b9b66dc8c
b9b606dd6114af3a1f3f79bac8e733221fe8752f27d85cd66406f1810dc144d3
b9da3dbb187155fc0dea9a1b6bf304cebaf948128206e2240d79a70fef513718
bc707f6c7f8e2a9e6d681c535d4144e4db13e4f8f935cee3bd07fcc6abfc138b
3739b5
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F6_0 /SOSTRQ+CMR10 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /parenleft/parenright/.notdef/plus/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/equal/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/bracketleft/.notdef/bracketright/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font YMRXOK+CMR7
%!PS-AdobeFont-1.0: CMR7 003.002
%%Title: CMR7
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMR7.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMR7 known{/CMR7 findfont dup/UniqueID known{dup
/UniqueID get 5000790 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /YMRXOK+CMR7 def
/FontBBox {-27 -250 1122 750 }readonly def
/PaintType 0 def
/FontInfo 9 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMR7.) readonly def
/FullName (CMR7) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle 0 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 61 /equal put
dup 49 /one put
dup 43 /plus put
dup 50 /two put
dup 48 /zero put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3dd325e55798292d7bd972bd75fa
0e079529af9c82df72f64195c9c210dce34528f540da1ffd7bebb9b40787ba93
51bbfb7cfc5f9152d1e5bb0ad8d016c6cfa4eb41b3c51d091c2d5440e67cfd71
7c56816b03b901bf4a25a07175380e50a213f877c44778b3c5aadbcc86d6e551
e6af364b0bfcaad22d8d558c5c81a7d425a1629dd5182206742d1d082a12f078
0fd4f5f6d3129fcfff1f4a912b0a7dec8d33a57b5ae0328ef9d57addac543273
c01924195a181d03f512ccd1267b42e8964a17d77ba8a5dea3d45c75a68933dc
c0005d477ed6e209373c79699138b13fc80321e667e1f7ecbf0bb8cb6e2c4788
aeda96a4e6fd2cab7fae700235e6e7fc30f59fc87f10ee7bd61daa12b6b222bf
fca43743f8b49915e23689804a23211a3d3df527941ff0728bda761f3eda1f47
f41996ae21862f0d1f510d460e4db47ec5662f6d1e1b2aa1698b289e222169a9
c19f0a4b8035133e0cc5a3fc0964932c4a5eabb5851b19042cf0cf5d825ea20a
7ae717171ad22a1b09f2b52b886b68a9d3026a4f77e8bddc71ec0209f06b262c
93e65f3f8099ccfec988631e22936e3ff6a6ced5578893299e9396d58b1f13c0
1ace1d03a6098d6bc396e68a9560ed8d5aadb794c32ff48f53120d0b962acd3f
95b5067f637c07e494e557c5676fbe91ee91fdd51acaaeb262c16938686573f8
beb0510f69fa84c9ba342946a191f91376b8caf69a80500c56eee5a816d890c0
70696b91b8606aefd5f0e460c09bb5c145ab55296f08eeeab557f00b6a424e66
8bc1dbc0b88350c9548cd806baa6d2615f24efe910ad0dc97544641486d8338e
5108f69742195a53667975340ce89ea878c2e0a6bae1dfd14ef93cfe9f8c31d8
1bd2e2a158e16b953717d3499bb93e251bfce87dd37f0ad827dbe55499ff29a9
7e15244925ceff71e092504923b32d4d1293cfe856786bce0ec278c5ec40debc
d4db9c135adf4a366880efade2da3d6841dab0dfcecc063a10bf23906f62d676
bade143065be5cfd1ff40fa1ed01c2a1c51d3093c9e805f56350af427a7bc51a
a266003ddff8b664318aeadd479a277bc331d7c04064ce447e795872be9544ae
4f5a90a845c92ecf90dc3deb9328255ea8bd2f3256c0b81729b8be1a9dead2c5
c7e428dff0ed6defba1966ba190705121c528e32301860de89b7544c6df42f01
f6e451138e4c92ca1c820d7a4bd84d1d6db11fcda5b1a59cf0fcd8092b5ee9b8
d67641b3bc0a6f45cbfe47781faa761ceced58b749784102c9f357b49fa407c8
fad53e78da43c2aabfeb35d1048394f4ef2177a1d35ee9930cf914d8c4a5d876
942803f4d1342c2da38265c2f1bcd3bba3083f2f5289e3ec973f8e44b3716571
c196c2119d8dab1c08b32da1a0a8087845edee2024f5dc988d1690a22a336fbc
e1ae988259d42b307b2b4e2efafdb580c53ecf8888273da081b7c7494afb1cc3
0a665dcc87432273706e82b0a0328231097b33fa3d45fcda6aaeeb0234f5d45a
4eca320a00aff54b7e2a7781ba3ffe01f416a4e8ee2396b4a0860439aa1a3bf4
0ab4044105299a50790e0b37887ddc5eb56d751b46ee9cd8c732fa8aa194acb0
787e6d36c2063c565e4b6c031fce7a568f79f7aea42245a5380f4710f8a1e6c5
e4c4b7c4be42886abd0ee7bc8ac3539860905c5e0f1aff9afb2ba55d9e2461c5
582750436a94da470741652b0a3959241962fbaab6d7ced09598ef0e0f9fd7eb
1c48e667d766fc0fc32b3daa1179efff8174e5cbcc9c5d9333e9fe0b99557dd0
6ffba1408c09f35b0e47dd5d78a3c83539b29ab67d6970a761f407fba0f87e22
cabf20da1364c509115f5d9ed165957ba254955f88db66ce1c1a5fcef091a636
26c0582d1aef72e389b1ce95f83ee4ab0f1f34260847c53f72a55c7c369ba80e
99c84c296577c2a61891dcc398422b72d4429063e7db9ea03385c1760a9b97e0
21b4ac3a307b75194c0a1ec3a2d0411e07db6a7d7b7133575e4200a9279ddd28
fd131859a500c8686e30d657c452e88f53e13f007512f900dac40cfd02ec975a
c51fb0b695888f69916eb4e3d5ca3dd9bdb8daa0c79829eb937bb573af3de86d
5c82818295bf75116c5e47684ec81fd80640fbebe0281c9790730d7804bbfa36
1593d91cb10462fa4d878127122aea08b62703aaa6c536e53fe4e5eb6ebf41a0
b97b9c9eb0991f2cbb9931887b9b45f688ec2ed652786d4e3419ba6bdfe62814
0077139bb96c33304df910aa03bf9fdbe6e15c45008a19b3720affe802b4df08
99f570fdedcd74ed79dd091adf6fed0f3ef90a017ba7fe615f97afb753f6c0c1
aa0a5b4499ab2e96ee74d14911981845d3bdee01cb0b895d818d66c5fae756ea
aed593abde6a3756615f61c9c0f3f5222d7b23edd3ed17e6a71b2d81fa150af6
3ae71c624f97db5bf12911ee48adbc07d4415802da45ebbb94c4ffa7f755679f
3c6bb571a7004c19c3b342abe6d6ca2a6aacd3ba11680ed6498c270c2405be40
da3a6d2e2e862f719725aa706c2042802f1b0d5c66e9e5754a631e97bd0e4b9f
e5f09a68948d76785d6d0294350cede72a2272eef896b7bf8c3b5c38ef35757e
eee55b3a1f2b4743803af4b2462b224e100ad0d31a7feb875a986d1997417440
53cf7cecf6cf9f6ddb2b3db0aa56c413480657a050d0e033f27cfb02a0706d99
3022bba5be556437e7b6d7be19c85b56589eef952ea674bdaf46cabe7d72d5b6
79b9597ea0a3b41866dab5bdd0d52515c883f87a1ff585474de0517ed43d8e50
cbef44cf6c00e4f44c115470c759c6704ae3f60c19885f63de519d3aeedf006a
93e9e3a8df3ad5fa20ceab9ea08910e8cb5c353a395855d1206a8a02529bdf67
235def025771b59cef5ab8a891e3bb809ac1cb6ed3d3a043039de8ef79229e89
08ebb26a232bc7e2c7c85c99d67b93cd947f7995e7aa955dd0bd0f4ff8a61adb
77456592700856fbf3fb7c20af7cfc495d5a64ace79c30b5b56fbee664564a24
40ae7cef8b1ebd86178c0b2aeaa81abe9b7977f016fd10110c4b9f0fcf21f2a2
d50e30aee8eb33f803717604972e46ae5f1d584196a1467df68b355742795e02
107d8c573ed4d3327a4f9571e604a7a77f71b083a38c1b229e2085fe7249c97e
c9dc1f24a73e73e607deedf5a3060530b05940a8f9bac8a835faa9e810b77b49
bd8ed8023e13cc7905e782b26fd043b4ddec831f41323dc042f93feea3bcc122
528811b00ac1675fc92c7eb6fbf7712e457c206e6fcccf9754363b693f588a62
cc3483ddf47d74f7659ec0fe031802d4daffb74ccf317eeb26934c645acd7df4
328657f39b112eeb34a78e832eeebb5e25cd2aa5d01db316cb44d97cef5a3fb3
ed8437848e5731f001ad0c2a0d443c50e331cb6a5df989e00b7a4abe13f895a0
dd06ea923e1df114441a9f3f505fffef74d06fa1cdf34b8a95904c8a2763aa8a
f5b71d00f5de09dc1cdf87a08b6d181453063e14c12d9d8cd8237c918e0c3b7f
cee25b523103e5daa28b9560f40ab540406fb6ce6ef8681cf0bc2ed4c556d6dd
462bcb773313dd9f97e42952580f231db8a6f9a239a5737a34f1588922b22362
e20f77034c7b9e63008646804ead0000e16a08279bc68ca0518ad49174b9f61c
f9321bd754da6e7eee2eedab832084bfcb1b957caa5fc51e13f018df90b8fe6b
cf28ad46ff6d0a6ee3382a9efc1c590033f9222e67007ee9335342d8ac21cd97
f2cd73de38bc092bcee3dd860d96956998b8d9e94437b9c91644fcbbf9aef323
e5aff5dbc06f45fb4d5030d33070a96eaacc8b455c81c4d9aefb2bd81d3796ca
5f0bbb51f7087a8352c4890dcf1869446f42929c3d7ca0a06e240332621556c3
9bbe571ff4efb51452f075f09a5eecb95db437322386adbf87f0ac0a783714e5
b7534516bb35b0a3954f9ed8d0ef55ca3a3f6fad710cb310575c0ffeca15f1e5
1f9f718a02a6171750df00ca743cf5156801e3b5c2c7cde1522c76af378b0f45
620082c5e6ba5a35143d1af53ec39bf9970799f0c5d69c14f8a32315bb685312
5241b3ec3e32c4de0683084fd53f6c0f2271de280fd144ea4f8687f5756bf503
345f7d1fdbc79e23a90c00a5604ebf88fa304eab078210bb5f43e5acd9423ce2
3dab67eb4b4f0e312ffa61bd21ed2187d49328604acbadd719392e87c752a3cb
a87931076a07a6f16c6e974cb3f760fa66f9cf1680aa8218add67ecdaa75bb8a
4ab16a7744cf183139f0c84b5e57374cff0128b5d2bf6b48e83872c57f17ec43
2f8c16c7065f0885abe9d1e321130cbd84863167c3676020b7d262f105b67596
09b6fbe256646f54b95fab452486a78620d1124c5a43eb8162ea0ee010ce8f90
1829a72375fe65a3e8dde007e82a3ca2106d06c57d1b06ff1e7d898b3c7f5ab4
b7310eacf4f8955d37b697e36ee885fd95e6bf0e3d103689f6eb637e1e2360ad
046f4d60b849e0e49247438a1963c5e0498d52c228661101b40c310f3fe295e9
3e2b07594b071b435a148525aa9473142970d2cff7de78f0f6ff484f174452d7
68844cfb02898c87db11e2a9a93f0a462ceaf640dbb7909ac7c36c2de225780e
13b557e075e7c64c02c05497a096883761a0cd350ae5d119c8fe89623de26ff8
d18e16b8a8638d9c8961fe0ae672505971b6b71d13c2661b159fd8335565a69e
51366a92077510ee8921b50d91a6747fe5594c2c2345eafe7683cbd6fdb8383f
800f40d03ce911ff6d3fa9efc3849ae2c2b8fdd3bf59ee9717c037d55e553087
c7f14d60bed9582cd9c9f66f027aa69a090cdb4e5d86a8fedcfb060e4353f0a2
7062d6cbd3bfc8ff5cc8cf7b88f9c518322c31dfa354264a52ef43752609fd2f
448d23b065bece937ccbfb7d1e4afb84e9e2d32d6f9d189b7a4fce595496435d
e669d4c72ffac6eafb204b195eb5a687510661c8431e69a17b8c063b01e1a4a9
12078460a787ed3b0a40b35743ddcbf76b89325948e01094904724eb4ad9c4f5
d493974fb53e4b2b810d1c2b46dbf32e0b254bdceda2ffd757da0f0edae9de57
5a050c9575631c5110a2fbd5528e14a690e754a4319eb5a420dd3eef72e883f6
9b96ed8a8c3b46d01e47d6a7f127fdbe1d3ab2c5a9a36415ec165887cf6e7c49
bcf55dcda8a378712fe718310887fcba7369a64e2462709680d270b73c5562f5
3023c991a94846ebf0f9b327c7dc0159178fafc8d02ca7cba1a3c416ca82c254
a62738bbc97095a476207395a72f008139c43d0641fd043908d427d643625a2f
0739a6fe896e26246bc5ab3113de73d18de79386e17829d81e117014b661d521
5cedc01fd068be01b9f4cd9753721403dd156f0d0909755adb4dbe047643b25f
a2fe2f54866fd0162d57337b84ff96e1a9b63dc5c1d677f62ed08c73c5c252e1
2d961d887931c0d0b0dedd663ccb293476a764a81f90debfc146068cd997ecf0
5bedf0be60d90ae033d576c0f88c3b837b96ec1b187e2299eb69d4f7d963deeb
cd18486b67e198f1db3d2fcbe1440d6f627b002426735e2a5f8ef9e8b32f8b68
db5cdd16ef24176d265a684e81073b07b3b623b4414736423fb61fc5c72f12ff
655e211426a603fcf42b895fa9eccf970ed941bd01c148a6c1ee547f0ff22010
c446b360f282ba95ae7020da70130e1e8d39b7742c61a963dba77907d89296d5
aca2da6a77e30afc1e2e11fbd9cd35e60bcc74e1a26dcddaec6ccbe77555a863
74148ac32d2fc5cb4235730b1c332c96ceb14763d8e6d41b6fbcc374161986fd
3541d1001c8f7a182bb02be16145150cc89331c803e0f6ef3f4341f062b51509
7858273165cc36e2a580d339514ce7a1056c61504660448e5d88077d9e15e25a
f791b229ac8f387082a65b870e77e9b8cd2a28ab22bb5b26ab75a23ac92a039d
729a75ee2dcd098a3d98a8b5227243426e7367d51bf684f09ccd67d3f8cf6eb2
a9aa457ada3c62b2ceab610bf3797ad987e21b2b12b2f87a1fff7acf9dd4db2f
46349390e8ee863db936ac6fb1a8ac17f2f9a4d50eae1d66d4cd5f939059ebc1
305848a92534b02b4ddb48037477ed1820d08cc18bd508287df96c80f3c4dabc
617e42a3fd5e786391336e7b2ba87b9862cff39530c3a89aae61868f491331e4
6aa6e35c1610120368b90955d16a09a54801cbc4a98f94494c8251d6fc8da168
29e87f4ececea8db16e3aa4b3e0b30b574a65fe30d2a604fa7083a35bc0b894d
ec9e9ae37d917cf8e55a4ebb55c7f78eeb2123df0d51d2bd0f43b0969e49bf0a
b97ee66f1bf70b207c9e048ae2244b31136ec77c78399cba88edd539a4e107f2
7b615090b56205174b172f66116dd106182c308f3ffc663970a86d38902d367a
1055cec8186702ea10982ee74764a2e80e8b801f1a414ae7152534093cdbd07e
a86cd3d6135f32cbed9457b56aaabb644d4fc3bf1fe4008ae553db6d65a91bc2
22c3bddf0bcf3da26d01aa39938a63f366c9627c85873fdf0ce595b60a591d51
0640c083025d9bf5b419503268a52fd757eb822958f176dbbf93590ac9fc03f2
d92bc0933b6e4b9cdf39b84c81c1138cae2a14ab60ba2d8d310c802bb103c1f2
979bef18ae6ac5d0ccdb48f2f357745c8cf7eec6d0f247c04a83666c19ece5be
eb4199f266f4663e613544431024a936b9e26c6790befd95b62a34ef2fa12a13
981ce3244de01baba6fe6de2642407b393a82412308c0465e6d66c376161dcfc
ae880d281bee7733885ce9995c589ee341c8bf9b7f349b60cc5dafed967c9376
86e383da3231bf298f0b9efd859f64bd36042e3746ba6b43e62fe00031d84a35
649be618659c47c3b189fa1a837182ae96b9801fe1007682541bdfc0df9e4ec7
cfe87c405cbd2503c6078665435fec3ec3132458f5386342f2b827667b0ca59f
6e9f511eb25a4ec6720952b38f6e9fa67d52bd9031de07427a0de6e999175fd0
9c8cd79ae7c2e72d0fd30845a3f56b6ae6cfebdc6d6e6b22921bd735a76af62f
328c7eace3628b8ff545ae8539f38823c146966d59dba9e77e7c4e4470ad9754
1c54365a25f1fbd048096310fcc5746aaaf27a339f9cda5c15202a9410b32f30
ba1ca539521d5b9bc6a233c3d52fe063e934d9d6aaed91004bdefcaf5eb37f0b
e13362ef25421a4024aa4d64b6ec243828eb73938b50ca5763a659fff03a3295
d14e26f2711104cddc3498f59024a10aa8565976b3c2c648b606b91753208219
47720b2b3f8faba936c9e43ee2737bf026b7aea9400d587a110ce4fbb223e478
1248482b44258c765a7e574f8d3f560833c533034e0b4685d3819c39d00107a0
0a5b220c22bbb5726dac659c8897eb98cb7bd8d4fe334c1f1a378fe7679c9dc7
b397bceb520460514b38b11f5cf8f0eeda9580663068f5a0b120803caeff3814
a1850d7983d8c60a3988cb5cbc50dff9ec4486b95eadc7314cde31cc845c8524
0010b043be4662eff36c4d51017a8d2e1fbacbe2a1f049dbaf00b038b866760c
ab2dd9cee00225da9ea54f81d342545692041748a9db59172bc0704a7d530adf
c9b26d70be4a193386a8c95985fd61a2730cdd9fc204b52a5351594cba42505f
5b824857044212c4516766e62060f0be1c7e1b11a88eec5b78ccdb038f2f0402
7970e30a9176a0690bb83e9b7a1978ca12d8c7e575d0cb705ec4be4099237577
d03c34e362102c056d2a7daa70adc2854e917bbb66f4a045808840664ea0e067
0ea12e1d606422c5b5831218a8ac720be2e511d81a7372ba3435198c532dc355
14c910175f789a02e0ff60cc46230edfe5bf907bce008f3c55dea855a573657f
2a1fd06fb14bc3d1dba6286b60b080fab1b76d7e03b03af8e38330c5056cdf7b
8e94e1cd33362d87136cabd43f1781f0d9835d8d020cd501c5b4f3268a8831f3
b9cd492e534d995c4f9165b1ef176d0b6f94b31ae4ede823f2d2db52a0947ffa
a9702e5be4ee55b1236a7e230f3f2f59283a035dd6d5df3524fadc8923cbeec1
612436f86318c0a3732d98d1ecf8581f9fd6634e8298fd3644282738df417b65
8719bad3866acdc51f290c822304aa4962635e328f2d2507650e6aa5a65973ed
b9be2e4ac9e2b9d116d9dc22305cf9ca39e91981aa60d162bcecaf5c74709928
b4e13c75c67bbc4f250f2a633bc59d5538097eb59f02d5a26b0b27d5bd41bf02
b451c38c009a91149fba675a6a3f6cc22ff202c19104836bf0b41fa39312fc5d
ec16cafb05d2c4f6095006557b50fc52ef6ec557c8b6d06e5f497a7cfbeda91b
1394fe0799bff09fa84fa15c00e90ab49f5649b1357cd83a43df8bef1b677b77
c82e667309675b162d466dfeb64aa3496cf5e8e99b5f16f4a8f17e57c047fbe3
d620fd6453d7745f53d3b61937a0898a32780044a3deb1f8f26b64cc3d303f11
a9993e750a8b47acea60c738e3997dfcea0c3d1ce993013243ba90c4df3007da
70ec6c445351af9a0df845be70d5b9087944680bf7da8071deac3e627af876cc
a73d46a82ac0342e29fccc3759e877d1b233a9b4bd6800a7a38290879dc712d7
d09d54625c52d0645a206e7abe1fc92cff6a32e8efc9239ebb3e5827ef1c393d
eef3bf5f6bbecb9cd68a37cee2b29fb6f68517b80e9ac08a5363c789350969a8
7c57f8d6ba093d9ce3eb8c164a838f79c2003d0ee1b89c65616a3273a45dd014
e5c07c5c90fa9a46a855a2f87b8f899f61d6a850ce9d6cba7b324b402ae44cc1
76ece5310e588be6457e57b9c4c26bda97d0b30f8328dbc3b292a63e78b9c84e
73c7abcd8e1a8cc4058495ba1a624d378757d8b944b84a70c1b82fe96e0b8143
26de0818693d04f7ebf101b5483b19e85a53ca4cd39d9fc7385149c47af9e812
23d8b310de30e585be28082a9105463488e2fa0440efbbe137606dce51195491
25c5ee21eed430405127721aa11376e4fc6fd17743ec9c719b1c6086f15b67bd
fbc9c6d8adfed843bdb9dda86a92a3d2e87be556892556a3e3cf7292b5c81a11
e4962009562af3c11a7a88c0b4501b7964952b1a6d71ae631f8cc943c5971767
8367f6dfd697e0775d22ee0e63a38f8271e52406ca47f5bfcaae81dc7d5be19b
d6463793c4bc
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F7_0 /YMRXOK+CMR7 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/plus/.notdef/.notdef/.notdef/.notdef
  /zero/one/two/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/equal/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font DZZUCU+CMSY7
%!PS-AdobeFont-1.0: CMSY7 003.002
%%Title: CMSY7
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMSY7.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMSY7 known{/CMSY7 findfont dup/UniqueID known{dup
/UniqueID get 5096648 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /DZZUCU+CMSY7 def
/FontBBox {-15 -951 1251 782 }readonly def
/PaintType 0 def
/FontInfo 9 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMSY7.) readonly def
/FullName (CMSY7) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle -14.04 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 49 /infinity put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5cd06dfe1be899059c588357426d7a0
7b684c079a47d271426064ad18cb9750d8a986d1d67c1b2aeef8ce785cc19c81
de96489f740045c5e342f02da1c9f9f3c167651e646f1a67cf379789e311ef91
511d0f605b045b279357d6fc8537c233e7aee6a4fdbe73e75a39eb206d20a6f6
1021961b748d419ebeeb028b592124e174ca595c108e12725b9875544955cffd
028b698ef742bc8c19f979e35b8e99caddddc89cc6c59733f2a24bc3af36ad86
1319147a4a219ecb92c71915919c4ab77300264235f643a995902219a56d8626
de036db2d4311c1c248ec419306d20a71c6acb4169880192724f0f4acfb4bbbc
d1cc3226c83c21fc7a7906a0253dcd0ebc7254954f610261c83769ad2863e979
a7ca91bee6bef18947b4e5dfd79576ce80eb6159249d8a53c7f018cbedc22843
9fde588b71f0480e4e4ffa8ae0e7c1999070bb3d69ce5d1f51ae3544d15ada53
db4cb20c7c5136dd658ca4d568f3e65c43198f12121843226cf158e6d79a47f1
ebe70181d64278201194071ceb579b05af270045e75be14d5ffa484df288cbc3
36a92b6313e162da709edf5a62b645d011bf7f9d05efcb5e6fdc34e4b4e9ceca
a00c8c47b053e030dc5cfe5e2fdcf3d0f2461b1aa24c9c7e6f2f07863b321b63
ba3e88372ee6ed4262be528c02b17bdee5aa804501b20b5314c42eb43917047f
12cadd2f8d0777b8f21b8847d13c1a23b6e99e2f5bd39934d8bba76a7abd7a71
e0d11e2c16490695a5b6cb82daa3167aeaaf78e1fe090162982dfb4e488f1217
9316caef1261a73f11432aa58b10dd7f00fcd6a86902b4d6952cfe27eab07598
f29bff3fa728eba379121391b8b3dfd3f92f2470ec859d73c5dc72cf881f5343
f96f26b815d3c6cdb0425acb1ec68e068ae04abce31b56a5f50f2948c9b3f8f5
7161951b983fc003c23bd7091f8e90a66ab802b2a2ad2138899911c2b727287a
723e30747e1a8740024237d2fd9eb4adbc3eb0ca7405abf0aecb58763dd6bb9d
cc742a986308b7c41e11f1c7e2e106b4befea2682cdfad8599cf7991c6250f62
a2f9b977e1f8d0626380327f0a4174f135a3e5e4716d234f3a4a6a06dd929d87
c463f55ad0ce7fb6daf4243448bc5076a3082df0565b2819e86137c7de356665
964cd48ddbb1bb325f7867e763865ea84cd57cde5f09374263ecbd8131a1dfc4
276df98e18d482c5d509ae1d570aa1b36f2080624b50bfa9db66ca1e414fdc91
6041781b04327ad3cb6c0cc1dc36a0dc84787d4edcb1c79eebdacc9663765be7
5e86f1852ef22202f9fe63047663b824de2399ff9bd6ef3b9a61112433fabdf5
a77c8d12349778e0f5dfbd0cffcb00aa0aa78411a928a68d9894614063ed52cc
db6e367068d89a5a19667a7af23f8a4bca1b0b14d919fa248859f9b64a6f2f8a
71f2cacc10bf94ef86048ce6cd08f2ee2ef33166f1bff7ba840d9d924a144211
d3772734b8b5813ffd107d44f22f99267f0c84c85a3d56979695a6e2cdaae337
b7457f3c657b7c5bba3165c3fa20c8e2804fd151e2dea6b55caa88860693a398
b3483534c4da34e82b13208d7bb0d6d99770694c20a57e2e1d99f4a1f86cac9a
520b4b63a6b0f0994f34289f0dc7e955ba6d0590b9d52a0e3708714b2fc4aa8d
3b0bf0049e1128912d148638333a01363c3c2f84c499c2591f9ef9fdbd3ab217
04b3eb446ef546743a2305ca86c539b99d26c09f1a42d13ac9770c0a54a3b98a
578eed1ac605a9f9074535374ce06ae29a62d2a05e7ce3693f66d1e9259421ad
31d3e4f8df5927f044a4161f91193fd4e20eb635b544ca6fc6d08607fbff7328
6c33518a7fe40778b75866376edae04782cf1fcd7014cd72843131db5610b238
d98a6d9ddfc02ede5b7d3cf7e337fd0ddabb8d44062a4cde377e56a4739f9fbb
3e20b1a0b0c98d8caf7d80deca9c17f6d8440f89c9ed9ff6e70574f71bffe481
c7aaebdb0885e9c4bfccec21d658393645273ce91e95eac26d082629ee8e4abe
10cd537716342133ceb4ecedace1cdba1cabe09eb3ce04cccfb385869756b9ea
4a96e5712c838e55ad5ac384dd5b9b4ad5bd514b19098c9e2a4c9738afe285b3
d3a31940308db096c815fbfedadb67077cc8b046b16054e1e56bef95138f9632
989dd29bbbd78dc687f0ad238a1fcc1e9dc9e97862c5608359814009abc99e6e
6f7b9ed4d316c6e461f776fb586990b1856b249dc812b06907053d07274394e1
fb045045ed730f9d26083e23e69a4dcc5836ad45cc21119148f43508e9264263
2bf82e1c7331ef28ba921ab18852390c505aa853df498cd141880b04bb4815ef
29877b792cd1e4b29a18dc0ee9b63998aebb921c9bd3a8a9d2e8a08298e8f000
d38e8054dd1613ad739f0439686f711c9d93566123e2fb61146910d7c72490fe
951703250a6571c0232a1dd62132fedd34ab005399e522ac1378534df2a647cb
641ba3f482c12b88d7bc0e94b8641a2e8d30729b4d561842da68517ad0be023b
37f5e6ed0058ce19ec03b5624789c78065346ffa78f5f075245dde048c27ad65
d65584350c76ab9f690c556e85329a885cc315b0bf3d36f05883cc17e19046ed
257fda641fe89bb3ac4621cf40dfef1a077d7da88a7145160fcd1b95ac7962a4
866157e02169fa7a73be4bf6c6422faf295017febb1cc880169c2865c74ba2cf
afccfd98cd1d9658742d7d5624e833b74c79a4da67a6d5d358a3f903bdd31534
ddd6cf7247e65b8bdaefe3f37e57f1cad40c1a0133643cc310ae8744a3691774
5c5f86b0a5ff7e83bf2fa99f8a91cca68eee0e9fa69a7f3261289f07ef5632da
bc4e08353e44f44cf86417cb759a4e3785043a7e25c78f7c34fe3d08522fd5df
58de292401e849d597e22d0b6f175a926b7e9d25450d913afbcd4110124002a6
e4cf252126ec9fd1af9685953366389fd66cfae96483fc4d529b2de92c30a946
f96e021d159c002759f64777d1eb75eec3065f2a8dff62e41eb35805ae77ad3d
4159713efd5c3b42a3d9c5cc10b4900d2acf5073e73af7ea09c196b7beab796b
90e7a05860a704c6978a581dbcb2a4297b9771627564f96f9bff0767361580d2
16e1c5852959ce3e36d021eb580de45d7c56ca6df6070562ac79315c323d0f90
e8acabc2708391d01aab40f4d618e6426f863d45bc1f70561f35dc2543b1579a
bfc3d00ef11054a96e88b4f32a710c3234bb4c26927da4993556cc20fd240231
c6309be54705011e15f45eeb5ad4962ce4b4a7799075f7bc92ea55f6a5d44346
44a5e5870ebb636c017c884e7a099e4cd6ec1e8b6a1e2db3c3d677bf3ee74f60
2227c5882270f93d9f0b8d13e3e4b9797a21a0d3a1010c3ec31ce86f6bf66b54
6541cd5c2deeef55128e17067fc9151875114336986295b2b9e11fef6cccc018
61f701058770ba19af0dbfe0970b1d21b25d8af598b12ffc69b96bea71c25597
ff32e4a5cfa1edb8bfc471b8c81288af8b47a8829947be3510053c41b9f5ebd7
49ab4e6dde7e57b2e382a25c83187252221d41a1aefee65d0d16ac5cfc6eddbb
3265112126f2c8e81288ebb68925d05c6944bbfd80f38bf1cbf69b7bd37224e6
8df20faddb8b9c3581883fcbd6e81a4a59976e41a4033f088f2b35792607b48c
e104483631ba24061c7aa28bfa2f7a3a6bb92df618b10d16363e66572049e432
53359e8536bd1cff9e0d6bbc8091e4441ff236d8a29a3d167245313f74c9c2ea
d730f55f4c06890f349d012a102bfe1d51874151eeea301b32037cdb968ebb1b
aab65d491658e182dbabe7d58b0cde9c2a0994c55f0452df89a3592502b44e35
c9e28736ecd35fecbea6669503ac87725b1970534831dceb2bceccd1095673af
ab80c4a4c0f7ade816512fc579657083d4882bd3205adc90358d305ab7e082f4
37e0736b06a615017b31b235d688da920c5f917000c6b49f7af209b81768eaf1
1ca8c44e0cad9e9313e1d10dc36bd44398dd1eac4aff1cb1e90b0ce84c671ce0
4ecd4ffd4dea5c32b3bc9d1909e2671ecb2b3c927dc43fe36a7ca6083be29c4f
7a1f1cc0b45e9468c5c6e2c08b99a591cd33d8bb243698388a467e673f5f1538
f6fa7bf4f57568d87825d23491e27c80bf071e42dde687f406e14169c16ab8d3
2551385bc5fa8affb6cd370cb68a67eb547bd2358c707e8f6b744714db77d488
13f2324fab3309f219a5e86618925819b5b54df5dfdffb0691454fa401ac8011
8ea8b30b87de8c50db0593ab828b4801623b27351dd5f0f5afbad313edd40c35
c2414dfe23c3dfd002afd053015368c2e198a3b292ac20768bbb712d446ecf1c
5aa33be5b3dab680e3f8cfaa4dd5041e80bca0585ffd10b249d1b2a54f709aa5
35c0a161a80d8642eb25c6d839a8fba35dea5a21de15d8da3b2076fd7fa09e11
04b0814b8b3419506d0762d202d01625dba6c57b06291d0973b497e271b94894
adf5038ba13b836a9476d118c97beef7ecdf7bdbe82d876b2b484f10ef05b0df
fd57cda6ff8af24fcc3a473216ef798c3eae71ac2805dddef0391a340605d21d
286bbe0542f3fa8a5eb76f52d2f6eddecc5b2f7eb11c437f32dd0cb2f2e803ed
256b094db683e07b8eb67083d800181c84acd57fe735406577b78c1c3ff91dbc
f79bd94f7cb8b23be481be96c0c786e07946dbecea31f0aa0df04e2fd71bf268
a6586a82eb6c6877931a544db6e2b7c25e151d9d99ca5ec7f3f26d650248a0c0
9802e8016185d8406c5522cf215ad8c86bc3843e2d163d1b07a049c9134ae62d
52412a5040b72175bf89f0b6ed29cadbc3d676045d6593a3b5fdfd247afb5f85
98bf90ae3b57fca572ac9cfe87b33cf815cb450c09c53a4c3d7516ee4409e649
dff530be95b181fce9431fc69ce47adac7bfe8abd637cff27f8cdac33076e352
1a5b60b9b41e8cfcf7dac5298d2bbb3a7cfa8fa96e1c81967408b21b738e79cf
0331a77e750a7c539ea18959c8086960e9d97a7246c37b6a47455e57488baa37
8128a4677d904dd2d9d416562db2af2af8f9647114ceb15bea8ac35ecf0d88d7
8810e4bc002fd9791717c4910ddb275492b169b03c59a86e2f5eda1b60cdb61c
4484a9eb2bc8c2ef497887fad8e3939289be8c284fefdf24038e4186584a3454
e7599baa22262e1c831d597bf67172866abdafd143da237226bf1ae20ea785ba
4c6feb49ac1bbc444d9cf42f194d775c2db80a01def569467a904bc1e05e6161
63f4f8615b5d71744c4f838c8d3b14311c08ea99ae3d3a2e101df7264def6e02
74d4bf8489d76e83a8378a8dbe8bfc2ef70fa61e2900167a5f9b8518fbc13ea8
bdb33afc79924c1169ea6549b51add46ff787051f5952cb6694d4ea8f1e7fe63
a09a14f2cb1b6757b3e3134b923c1efe10f1bda2ffea55c4ad4f721de8e52d8a
2df8efa2740a9e63c6258f815703523f3750511283bce534fd99b552058b094d
f93682a4bdd91ed47a00851883b3d45e04283fc1e2b54e194a69137786effcaf
8ed22fb553e6f5dfe466059d08f2d710a8ae0aec117ee691f5279f147ce0b795
4e352213ef7e0cc82032191592b5f2488186152ad9f9a1e38ee5082f0c7e2fff
62c63dc22fa61a6a313e7e14064467d128cb8918cbcc5ea56065f076730c1e16
2474f13d45d29da2f5ddf73b6584dbd42ec65cfc2dca00b147cdf10c6bc0212a
03357610e8f39e0814bad9bf134ea4a450c55ab24b6bfc5e7703f663052fdde1
42eeb721faf9d915de639c6f9c0ad79a6b4339364dc2add0b485c1f03180ae7a
192ec2c2fa8b60f543fa9ffec24d6b6651391910b9627d4c263ea482057d8cef
8178835e01bcb38162b0618ec9d803d19930ec564f483a8bb75e8c6a4aa1c18a
0cbf376bd1779196865682eb14443dd6f9a71f0d01f7c249cbaa7cc5ce84c410
b7c9d78442c47cf9f187bafbc501a59410930dc3f4a6af9765ea4adce7b92b17
9deb19378d826c905aa14dd2f3a5dab3374134c15493509c70b09c9e4dcea955
52c0b096c4078066ec8807db2bbb9591be8c31e595bfc72abb77ceab82cb790e
cd77d7662304a7b2ce8629e10c7d546e98ae9e244c58e3c7507f01be5993039e
381f83306d5dd02d8a69032917658753328c6fa79bb9596ca29b755b7c0e3004
6a5cbedc3cad92fb9d883c5bb2050099ec400d77f229c438c381f06f9cbfdc11
8009dabf2829ed4829673de8c17bdff8d1b59fb95d3f457e547fb6ac28f5fef1
d958881227b48a6054fabfe2e1ca97a8a322c309c8414019613880532453e7e1
2de355a4bcc3250aeb896921e4c0faa350835679975a141411e90573d6139275
1152e1c08a7dfdeff9d928131d7490ba19eaa63f9688695fe8dc6119b3af7c8a
84ad0bd568b61785db7bdab9aef54a0ef3b22dd8b3ec609378b15644fcac2602
996070ef0b1c2bf320f30ec4b1e21a6a4f2d4e35acf9050156b14647bee39dbd
95bfecfea7958a2a7f4bdbfbc4a3875cc76be42eb0edf50de11d6ca458b35363
e37c72fe8f5b5d10cd98eefb512687ac8b21da61a2c858ae74ad9cf5bdf15b72
9a4b1c5281b95f34b6d9c552d20b7ba393211fd0253312dd162e17837ddf0ad7
2d42ca2b84ccc3de99ffe394fbc669dafd811e7fc37ed583b93c4d37b580d986
c86c94c2edd4cf433373e400733acc7d9e7dbdc433cc29796e068f54aa3834bb
1303ace47e33c5543610a8a7a70f6cf69cd30e326fb6b9219f2baf0ac65f718c
2611c3b74f10679bcdc5c1d1e95087b409fe1c1b080c9f1e4256ac9cc139e06a
92160efa938069371aa9ed351e3880149b7242e4c4955adb3c79b4b4bbe98795
123e95fe68cd207fee4bf2e72a2cf62f68b3b3506ae6be7be4601a830bbf4443
f4775f136817f4b82fb0703365482f499c41aac92969f0c26b23fbb8550b5d03
60ad266f18f028cc6b33bd3e0661d46cbc8c05981eecf8d13d89824b04bd0adf
2fee3340b641d07cb302472bde54428be99d52e6f0d7830d334fd6f141e342b8
6cc2d17be6736c2213cef131f73720e3ce6bcad21a5f9165e4d12d12ff905186
4eac46519b80d519019b0a94ee96f08d2a69bec43de9b70283dc4638ec2ab2a1
14e0253d4dad1b6d0286c05ba7cda15d0237b74882832fe9d3c806ab1c6594ad
2f95b763919345e372025c3474453ed7154932bb38ddb3540d66d8d6f3874c0b
f7439323d1689a0a7742f3080fc5ab649972cfd87cf8b47b9d00c854e535a151
6fdd32beedbeeb9d3f50a7e76d6588d0849edb2e2dcbcface55d6cb2c6bfc9f2
ad38a1ff349a001514fe3cce4a02eb2d47a7d1c4407a08bff1bccecbacf0f55e
806f639e40e2826f82115af2b4b4b4dc6e227972e9c1e867ce65d9e1a3c2ac62
d324c929a712329eaca551bd38db9d1e521a8be5eff3c844644358d29b0ab446
c5ea487acda914a4eee008cda3e307877ff56688b125504a5111acdb831c938f
21c75adb0189f90d1a301ac57adc415f1af220960977f3000fc91a0a57114123
a164d4e7b15ce45e3ea4633ac3bc9153f4d408ac520228e9fef104ede98cee12
248e747df13c1e0a4805fa2088a6ce0679b7593e662e96f0c71092f1a952c7e2
85ac14ba1f6aa9097daa152b109050aef16a452ea380a6b3a7d4f858b819a0ac
cb67384b47145fee30b32181d66ff47aa65783fc2a345d78c21decc4aae701c1
b309ebd9336df1bd36a2f72072e86aa1b9cd98e77576aa3e6c4c5777a51c504e
719de547de8d7532f409fe94eeff703bdd907ac40c49b368a5a43dec49c04ab3
0b1d0addf352fc9cc09ce65805172bb61b16009dae258d1146c4d65231f47aac
0a0608d244c83a0217e267b28bf27bb059f27d3382ff123efaee36efdde70c0b
c64b97f05168f56c0ca7d8c5ff93a61e9d5ba7bbc4861989e89f2e5e5e637d15
1c2e73a7aba51de05ed69c473eff3ff7b1feeecb574acce3f55865f40bd196d2
048c7b2af2eb6ec67815d27aeea876c09617b1cee6a234c879dbab74512fe0f2
ff7860eebf6b348fe702d99ec976714b5fe29dc0f93c2de0addb6bb87b82e680
a33b802debc403a6a966da99d9a4c637e185f8145444f715d5e5df0d721338a0
d7ba7a72014195810da0a805c3d76ca3a515257cdf776391e67c7389dd71722b
329f384d02e454be43246a1167495df8f6db2cd2d165ec3b5c1e436b52cf25b9
3d0d1105091159e8780a5c9c06a95c08cb9fd4e36b965c58ec5bbef0cc17eef8
cff5d7ef0e4068909b5a67b1013c86dc28e439d6f06b053c4033846c8aff52a9
ec07138a283211e8e588904708b89a2b19c0b502680ecb7cef9dd5a031dfd315
f70c9c3e0913687d0a5a5238c91e5efba4ae52b74e792f509b21c6269f3b5438
70b9d32227822fd55a0d3879fd2e3494611552a116d140475040aabf5a51224c
014428956667a98ae65ee2dcfc762880ba829b94f7b07afbb8abd3f56d45379a
6f2b2535ede7dbd323d716b66ded14732eca19b12f1c22115b704c438c156809
199fa87aed655a23ab56ae75ef
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F8_0 /DZZUCU+CMSY7 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/infinity/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font YQJSDJ+CMEX10
%!PS-AdobeFont-1.0: CMEX10 003.002
%%Title: CMEX10
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMEX10.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMEX10 known{/CMEX10 findfont dup/UniqueID known{dup
/UniqueID get 5092766 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /YQJSDJ+CMEX10 def
/FontBBox {-24 -2960 1454 772 }readonly def
/PaintType 0 def
/FontInfo 9 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMEX10.) readonly def
/FullName (CMEX10) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle 0 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 88 /summationdisplay put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3dd325e55798292d7bd972bd75fa
0e079529af9c82df72f64195c9c210dce34528f540da1ffd7bebb9b40787ba93
51bbfb7cfc5f9152d1e5bb0ad8d016c6cfa4eb41b3c51d091c2d5440e67cfd71
7c56816b03b901bf4a25a07175380e50a213f877c44778b3c5aadbcc86d6e551
e6af364b0bfcaad22d8d558c5c81a7d425a1629dd5182206742d1d082a12f078
0fd4f5f6d3129fcfff1f4a912b0a7dec8d33a57b5ae0328ef9d57addac543273
c01924195a181d03f512ccd1267b42e8964a17d77ba8a5dea3d4218e6670ff47
3f5bf65481746b759c2735164f0c502031f2cd5b2eae42c94295ec426f3094cd
0dcc566f08f0473b81a3f2779feb1bf5ac434d644b071c0386265c59547b2376
ac0d6dc920bc06453537ba477edfa10c2b82335bc5a5859a378c33c59d163a26
754ea15d42e4094a65110ba4cefe76fbc22812e28802374a00490e464f2f056b
5a294302a66b81937aab992a37a5587576779ac40d8ca7d986f86726d68bac55
fcee142b44ad5741a5c5e0dfd4b31eed1de4c7d5509d783ba3255d729d1140a4
e00107ff8e9f11a1470795aee080ede57e66fa4a3484eb38d8f97b7694464df4
a2f87ff8e2b7229b7eace70592ea779a76ace2c7d487fe1531b5ebfec4eb4900
000c6d4a586b1a096b048e14d5e9c5353115449e8d88de18c65bcb576f706ce3
5e28edef3b15d27782e13c57fd4f58dc1009a8167080599a208406db1677a1c7
d7e14093036397a9274915d1ed94fabf12a279b781b1c529de607549a3114195
d107676fec2507f56e96e58f2325fc18294c50afae321688b862a75fec185d97
6e562cd4faf7131c83bd6a5bd41548b2d4b356854d926a6238a5cd4f7fd87e74
f55a42e59a28f8e869e1a5669c2dbc81b55b500947a429c180f83d045f0aef8d
e07a52d1bee627ca1f6a413e0e5c4606d6f4cb497af74885a9b0792497a22472
050cb41bd92e2fb1786acd38339b1007f5dbeee13e837a3e1ae6bd0f39f74ed1
9c762ddaf276a3e029fc5454a3442a1dbb494c7d9fb6711cb0e2a8db6278d73e
f7f61d750e7dbd90ae26e93aceeb3d6c5dd51eec99d16f3ab7b7b487eaa44593
8bad69dba7ed5b8f415e96cffdf60d88c75b972f0fe54552cd3bc8f152e98d3b
940e22c63628c5a9b34b1b3f4321cd3e3b676829bed50c4761b9ef09396e51a9
1fddc03c824017e6f0869d28131f3cda01888d9b1b7c2b86297dd550c6cb8714
3226a9b1641e96716d63fcdf23e3490e68b2b6e8c3e546f66549fb2d8853b304
1d9ed90c841f6ee4e7cc7c7ba5631f886679768d3430aefbc2eb5d764f873ff1
dd8b5a12cf89ca4e2349eeae27015c39dc77c9fbc38550ae03708ff3fe05ba60
eabd69adec0428e432cb4e0519017a66a5a2f2af8c41bcca915b3f917ff9caff
7d977fd3374edb29c52d74f529a45eab4549285edc924d5b0fdf20d2bdb8eb54
66a85bbeebbf1bcb7adde97ba0dc0b721043d632aebf59f363e243c5a4c705a5
c5ac1ead02f966e5fd17f976cb6ead54ee67544267d95e66ba844f14a457ac0b
8510be334bdd67e7b36975f0e8d893653e1bf6f94eb98590d795f812aca61ff7
71a831d8532ecbd6a22b8fbc30c8897f3ce1f7a75db6cc769eaed66d075af7ee
a5a0c90c9baf1ffb3dbd575668590f2652fe7bad21327fdbdcbce827eb4e7236
1dc9b18f628da06ba45f8318daa9d1e308e9b0fe169f17c0a91acde1eb27c040
881931c615e133b57b0ef04d4bdd90805ff6fb5fd9c44761dd54bf41036201ca
8acd305aa8427be4a4a10d64d6e5bd06324af696aee43efb203752d30889ce4b
ac378ce10498d78f9008d1d817c154103bc8b0e8ecad2b5b349042f32a001c95
bf0871347e3b37a0b34420350385573f0253f7bb26d73395a8d1def15b4ce5ed
f9abf6f05e277b8cfc502956ccb47ea1422c9b31305a5d1d54fb8dd543321465
3b3d40d337de6efaaf360a7c199ff5d51edc2c451181a0b5fa822bcabb25aff3
5f0e420dceba3728290b86fb8578154b369994fc71c2c351fdf0136cdd3a17ae
09a6c96071edd479ef699ff35f4fa3be0437e914e24d4b21bf35b02873ea1866
3cca453008bb4877de5aeb3e67b4a7c4cd4806a51651311f4e8b3921e53b380b
40dadf993a80cfac26ea2d8f2844833030b7f0a8f0666b431d07145b819fae96
dc78198cdd273d7886c1577f48f2a90b697e0a730ea78a1215fdac7787f98d8d
a3b34fa4bd8056eaae8885699bd44a864ce018d3fa259295197bd579dd980246
0019fc223a0aaed8315bdcfec3ef9d0f5b0d6ed67385659ee15d2d44e52e96f2
989c6374265f9643c5249ee39d495d44d898c6abaa27a28f8491ceeff6444787
5306c45124d28070011baad584bf07363cffe7f8b07e07f02244e9bf67d59e31
14e0166fd4042f2b38f3ae81e13edc599dbd82021a589c2baecfd0eab0adf6d2
85be89bec13a6617ab58114dc1dcec0ea1822812a77e74067e788cc4e8f463a8
2baa60486391e47614229c2bd00321e667e38e031d6c10183b256be8ceb90d23
828c9a76ec220982b825db4da9c204419236d6864e7b7f85c825ba955d8d1844
fbb2603be63e49ebbcb3e6a3c6e567b6219ca1435369e8d8c3986f66d0c76717
8a6c18753a6f33a079961d55f0dda2d7f05c619f0516c13b05ec2793e08966ab
40e19b9976d8e2ac8afe5afdaf6a0b4e42b25d83a514f02e79b869f55733c3fb
09357b888cc8242200133b1be9d759fc5dab8e60a0216931f17bfcb2b15a84b0
6e0f7cf300ac8456532c76af36dcc5e22ec7616d247ce32514d93ed1d2e2ed29
547f43bfe796d46b22a391331f14e36fb2402a5255d72c8ed63688e43c1b2334
c23408608c7844c6f0c4016f3a45d674db1e7b4d8436233a879786ae9a5d77e7
de9ef59b4341aa9e95276a5da13dfbfb4b348805f41dee4541c33da4b1ce3acb
4d4fd461c6d22b5658c95be3a6622cdd1d6d61d92ab98a1892cd3639975a8ab0
5dcaa4bbbc88837caf601ecacf3f14168b7476f146e8a277d8ce723229c6d01d
1f891ed62fe42de3034f76b13503c511c140797fa98b8239205dba23d0ff01d7
d1c8f9f301787e867b00ef2109cba37ac93c5a00f56f8e2e7462c74266ba1af0
51b6e07e9ecac2a2b025d2ac52887c5c0c42694b2a4e25f07eeb1d0eab7b5fd2
2662d99e66723c1ce4720282241b6166529093c7c4fab2da0a8a06a19ebf3920
0a0b231f8eb8b9f472d06c57eb8016bcba57301905fd3b80b0fb9eb33f488d4e
17b77be0c7ede603681b9fc64997dc236c69b4efe879b39317d90824ff7213df
3cb474199b8a69580161c3a0edcf1406329f3cfdb3969265c7db9a8280cd898f
49e485d10da9e0d7158c8ce55d061dda18b0c12c0346f3f73ab048a1d892d66c
590d469648537fee15691cc8911a8ac0193a95471459e3f4fd84baf247b3017a
ed00897b575a0053315be4c4b6095822a8118454daca15b5fa3a64bfb8b12165
b94d9e82d7edafcaaf764c04540ba6191295bf5c11e4809019792f00e9dcf3ea
5671d66f577a5a63e27e357d21e8995416bab9b34eb509084592aa8ed50b5670
9990ebce6df3f42de409e1cba095878d1be4174587b4d48cad3990d516b15130
e38e1e127d2c2fa22294b157dcd06c62bc0ca49f12665219389dca3819568c3f
15544d5c3b555fc1e54c977fc5ec0b6a5d6fd985671da2c47206eecfd22aa47c
f8bfbc6a099a67940c813b9f692b287966e013ee685a44000c00f06481b996ba
30f022ede6bb0c75a39d642c917350daa8662967ee40878202474f4b7af5950a
80e4e6c0b90953a25ef094f5d2922c1f52d56690ecb6fe45c25c9baeffa16901
b02276a95597cb3b3ae5ef5b51f152d3e539d81c6b0064be86f977c095ca5de7
697713d619e2371c3150bdfdb12364984e64dab5cbc03fac3782a3b0427c97fc
ea96efd4c98277bc417575c83e7b54c5445d37baffebc9f064e1ec7b93f9ad08
d219e3577415f2834d701386a069da812813a1f72b5c2c170d705a5d38b7bfc3
a2b9ad77636c5f451aecd8fcc0b8ce804702231bf9d7d4d3b1c1c2b612eaad9a
3d5d5937122a9c8ed6728351fe20215751dcd38472c5f5aaf66701e0644d391e
c0d36e1a2abb50b220b4be1c8e029ce08a62df3384abe942ba78040f65100cf6
403152684f6a05f885160885f95cf798cd427963770e987a169d0ec6ca6a2010
65b5b5d3d348d73f90c5e912b409955595087e1470e9cc45821c0fe8e4a6152e
ac6b7fc74993aee06334673cd6e9bb17e4db42eabaf95aeb5cbf0242151eab85
3568829d72b6860f1945a3a08415645e13c577aac28a02d969b5b76d20a23b07
f5320c18223fc5ea0a5d605fb116a95a20180738501e015ce9cef477989c2981
1c83392539a01117f39b648453367fd419588d3f7d868c2be39e4cc959a84acf
5e794031f9cae80e1f20eb28687b55b21afcd065b2196dabed2c462f64e4981d
8ad41d2248371a3fc26a0c9c567d82f696320ae66c0a4fb46c6228465938cd47
11fadfb1ed34b02ec50d65530e0800b25da83cb1b2921462407bccc9a4411f01
2e53880dc9663e8c6fc0f64ca3c6a136972fdde7bf94c3c5134f48ae6541e1a4
8704c7f4ce23103a6aeee50ab4370ba5c036b50f1c59e4c0d05e52761d72b4e9
3f05b4174ef8d656d249d1d97a31b5a6785e9d5041e9ced5ffdf7eace6f89e4b
9d1f0575749253ff91605a83e04752601e54956733ec48c134e19dd727d1654b
520d60aadc816b9d2bb7abde19e1de10116a7ce1b937dc6fe0bb484e50067112
8990114a67d00634d27fede9e0a37bf9228ce7024e08f107dd4aefdad82ee9f1
f30503f4e0d01f476f5bf6791376b1912e499d53bc2b90c73910156ace55b44c
642b88b593667594bccba5c47e6d51a1b1661ec37347f14dce62d029ea525932
e1c43eae793264893d04b883ce19bb550f95f104a165edebd8fcf2b900388640
2a3c2a3fb5e4e621f58f902eec799f5d50688e174ed6d0abd13113cc7180c3ef
e672591367eeb2b04d8eb452c7e22f8b0e12eac10af45f58c9d8cee4bbbeeb72
752741df707565132bcb1a6059073e71862057f25847bc3664ef88f7be5a1092
0dbff116ab0e650d9ce51387ff088294f5f1fa9c54b9f8a2c9edef5f8785c26a
5e8b2de6d1275b6ea46e79154f5aa33a4fe4fed43f558e94aa7fa790be337a3b
467261e1aa1004a77d902f5f0d9b2de0d0449f276fb2211c4fe451278bcab14c
cef640980ca9d82e215578d0f27e0f65526a3d553dcea54471e6b14ba6df9226
9e7539e9fb04cd719bce443c3adf20b5af8b11e14c62bd2e33bcf1ff7f8463e4
fe0525da785dabd7893b04aeadc1c4030cf017bde561edb6985279869f0ddb5a
da3ad58dc36c918ebef65e81f96ed77a100e21cb2f72fc558ca602d5a6ee3429
c5684fb7924d074d64c4cd10b9e6927ffed60ceb3134f5b42f58fb89b77361b0
183022ee0441abebacb5c7f5657299e1b6926c8e03424e0f8aa0729f389dd1dd
b059e77e7279398b688bc53fea6368d99e9621fa841f630a145904e78c854f8c
10bddbfa63a412f5dc7d710fbe35059f97965cb6fa9628ba79d521168ffda65e
e2d9eb03284ca7b60b313533d96a76877af4688ad21cd5e939e9b794ae8ae697
1b37d6135af54359f60601e58db380b9cc4fc1e0aa3a2c21b792fd5514854324
2ada685b4781c22501348de84f86f4be232ba47993963622d03e52522d113a23
c9584c25bf599e15a290c9448964abad2c5bde06fcacaeae8746a254eaa0a481
8867cb586382d0b1bfbd3aa4196f39c787955c7bee84adf0ffbc68257639f527
741607dd551e4214a5b4a551c5952683fa46ff70c5d4a5dbd42c38578be5eb97
b6f6eb46b9cf469f819893c02d51a44557bcd04445b27ad135739e232e540644
3110523084dd8aacb13afb24dd7d2b83722ae9ad57947f9e9bf60580deae5562
bf9c5c5d45a87673077cc33f4c6b6fb2a48e4faea4d4fe69c7468d898a7895cd
2838897a31e1f9156483c3fa387707092e9d1af06280229cb0254b085e693585
c339c1437cf75d1d4ae7e4021734a170746ac58ac391439498c88794818bcd0a
c4ad1ad4471f65e889e52f22201e048123f21409df402161154d1f8662f245b1
30f1adc19b02d207553faf5c20e16259a4d3bdeb87f74983a46dca97f52e12c7
607819f22bd813829332715a3a046ae3b1a6e974574d18bdb04baa3bc638afc6
a6419c0c73ec2671fc5c6f71a8ba8e566a0551202569ae336b819200246ef5f3
f5182714c33d8c45232ac30a5756560cbda049e0505138eb1880f4e3fd033ed4
e07f690cd53418626d09c211a46d69fb7fe59acabed12e5060b25730cdd12732
f38630e6d6dc00ce76fb776c2e5d658b6c99d0827fed1df9dd1dc521ae599797
7a9bd622cbfd8346df6b52cd99b6d5cee52cad9a606be1258b9849756261fc6e
5cfe52da8775186419de050dcd3a74dc3fb7b0ec59a6538efafba12f57586c16
4fe98f0eae5dc17ba86a900ac0b1669795885f89707c94e5ea3d5a4f9bc728ef
2baafd60eb48090aba350d7e9a9cd11e8737646808c802bfd6ab5d56db31b4d5
d484ec9c32a211d04428ce575bc32f1474470a57209428b50dec7aa09f4bf804
afd68de8c111aa335a218b1d3ef48e4ca78bdf57d7610e46a73bae8277a230de
e463bfb3e81d4196b094dc82eccddc4c116381bb45613be3b00c3c72d8535e04
0e9904a90adcd6612c60b3900289c411988639a45cecb6c2aa13e69b1ad402a0
b98b3d767fce2df227e944461067623d6c19c8fb4f1ce60977ca7a3b8f3c4bed
a6585e0ad07e0ee2268f5948f92fc71c1eab21fe8afec67546cfecaae3c201f3
0fb27f5b1fcdc5290b498dcf428f2d024126628e7b4273c02ee905dcde5787c3
c27b489dde79327e10bcd5eea7adcfc1dc2ed6f97090beb6ff01f6cf2f93c4c2
98321d695f2d3143f143c1ecc346458b76c77dceb5c6617f918ceeb736c95612
ceeaf60916e8b4377d5774abe5fea78d376df4f6d97c55448ade9981a6d27e69
7e73abf4eeb59b8938615de3607eb73a6b24f09d87bb7990bc2b74875c821661
4e616ed425093b9e437c39d5e6485c4c4376e749e88e6b86ee832e78beec8a6f
5d18240e4e6e9f43d66d7c274c27e74c29718b2700e503bde7def463119edc1a
3551bbd905001718b56a7baa79452feb2340d17edd9f116f1286fb4b16026541
1b31e0a0f318b99987b48b9f88744d61f76ccb0b005863ff2dee3fc163196b12
0ee1503699bc7f38601fffcf34655100259ec8b8f9a1e460d8d0bbc7c5563f2e
5351ecf1f0b61f871300a8e694b046639a3c6786ea4ad5e2ad561872f88fd1d2
5d68f7dae1df74df735033f76f60a7fd0f36a3de338f012de5aabd0df8b31f30
bdd8ca87de3734bc4cfe4def97e019312a3e2a814447b53580481058d226c673
b8911877c82af1f897a192c2cbe43b1beae47328ad8d235042d9be20686f4f74
258a4a8fbbc309c31875d100f60ede2e3afcf1f49688db83830dff2665e3e573
1e73af45a4c6e53361cc952a99fe50ea9b76942aa56b5d0835f60044fb36e68d
3fac78e633e07bdb25b7d0af45f3a8b56956ffc0a0ff6ac6d3a8afb9a79450a3
831e4e785b9af60befd0a96ef47f1150d7da311d235707d076a59b4138debf36
a1647a93b89d4cedf17447ee623550fc9d772c2e9dbd8f2367bb06ab858cfed0
463ad9c0ee03f034fd3a75134256f740611c4fe59532a57a9a6e21c10b6070bb
675477618447dc37fe94dd3d0d62e97aea73d4d0a4bda4965940ab8db67d0330
8a7b39fc42ee3624ca97d4a73c218a8eedb6e3e0c73d943be08318537e639dce
4f41e4dd58dfadfb474fc0f1cd987d5604a7ba3d11006b763ed08b3eabca166e
343d16237ca868fd7ef9de9534f252065f3dafd2e5cc09195beafd3f729de47d
99ae9da7d6bae168ad0de2ab7dc554c27f0b896534ad7bca233afdffc5b300a1
af3716935e4cd40a5755f57088ca31fc8e620900216475db4952a6d39cffdba3
44fd9ffbb81aea14304c361c8f21b5e505f51a25b86f38af17b96e5b5d145cd1
e538f79bd671bc8729d4a4e2d08807bd793b2468e18af31b95093c0535c81624
8102de17cc3c177de55101a444df6f6bda6369858b5cd532d2d8b9636c1181c8
e6c561a9741775ea8713914cd883eb8ae7c4fdc2d5a477d0e4c57ed95711bf85
fb089f34c79ef2342e922d5ca7a969c49dd44b449340c6db03aea1e552b57848
83cfe5895d0f95d9bf864c123c234e21f0c3e8b47a2663a76e5b7818afc18a97
5c30a09302494e846805740c2fd172e112b87e7889a4360c25b9463dde3d1cda
68bd63f6f1c8237916c5e5a81e2e012c841bad6830d906
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F9_0 /YQJSDJ+CMEX10 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /summationdisplay/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%EndSetup
pdfStartPage
%%EndPageSetup
[] 0 d
1 i
0 j
0 J
10 M
1 w
/DeviceGray {} cs
[0] sc
/DeviceGray {} CS
[0] SC
false op
false OP
{} settransfer
0 0 344.711 31.428 re
W
q
[1 0 0 1 0 0] Tm
0 0 Td
82.177 13.479 Td
/F4_0 9.9626 Tf
(G)
[7.833592
0] Tj
90.01 11.985 Td
/F5_0 6.9738 Tf
(t)
[3.009892
0] Tj
96.285 13.479 Td
/F6_0 9.9626 Tf
(=)
[7.74891
0] Tj
106.801 13.479 Td
/F4_0 9.9626 Tf
(R)
[7.564602
0] Tj
114.366 11.985 Td
/F5_0 6.9738 Tf
(t)
[3.009892
0] Tj
117.375 11.985 Td
/F7_0 6.9738 Tf
(+1)
[6.116023
0
3.971579
0] Tj
130.174 13.479 Td
/F6_0 9.9626 Tf
(+)
[7.74891
0] Tj
140.137 13.479 Td
/F4_0 9.9626 Tf
(\015)
[5.157638
0] Tj
-56 TJm
(R)
[7.564602
0] Tj
153.413 11.985 Td
/F5_0 6.9738 Tf
(t)
[3.009892
0] Tj
156.422 11.985 Td
/F7_0 6.9738 Tf
(+2)
[6.116023
0
3.971579
0] Tj
169.222 13.479 Td
/F6_0 9.9626 Tf
(+)
[7.74891
0] Tj
179.184 13.479 Td
/F4_0 9.9626 Tf
(:)
[2.76761
0] Tj
-167 TJm
(:)
[2.76761
0] Tj
-166 TJm
(:)
[2.76761
0] Tj
193.575 13.479 Td
/F6_0 9.9626 Tf
(=)
[7.74891
0] Tj
207.365 25.932 Td
/F8_0 6.9738 Tf
(1)
[7.942461
0] Tj
204.141 22.944 Td
/F9_0 9.9626 Tf
(X)
[14.390976
0] Tj
204.091 1.496 Td
/F5_0 6.9738 Tf
(k)
[4.235189
0] Tj
208.494 1.496 Td
/F7_0 6.9738 Tf
(=0)
[6.116023
0
3.971579
0] Tj
220.242 13.479 Td
/F4_0 9.9626 Tf
(\015)
[5.157638
0] Tj
225.953 17.593 Td
/F5_0 6.9738 Tf
(k)
[4.235189
0] Tj
230.855 13.479 Td
/F4_0 9.9626 Tf
(R)
[7.564602
0] Tj
238.42 11.985 Td
/F5_0 6.9738 Tf
(t)
[3.009892
0] Tj
241.429 11.985 Td
/F7_0 6.9738 Tf
(+)
[6.116023
0] Tj
247.545 11.985 Td
/F5_0 6.9738 Tf
(k)
[4.235189
0] Tj
251.949 11.985 Td
/F7_0 6.9738 Tf
(+1)
[6.116023
0
3.971579
0] Tj
Q
showpage
%%PageTrailer
pdfEndPage
%%Trailer
end
%%DocumentSuppliedResources:
%%+ font YQYTWD+CMMI10
%%+ font NUMAFF+CMMI7
%%+ font SOSTRQ+CMR10
%%+ font YMRXOK+CMR7
%%+ font DZZUCU+CMSY7
%%+ font YQJSDJ+CMEX10
%%EOF

%!PS-Adobe-3.0 EPSF-3.0
%Produced by poppler pdftops version: 0.57.0 (http://poppler.freedesktop.org)
%%Creator: TeX
%%LanguageLevel: 2
%%DocumentSuppliedResources: (atend)
%%BoundingBox: 0 0 345 16
%%HiResBoundingBox: 0 0 344.711 15.446
%%DocumentSuppliedResources: (atend)
%%EndComments
%%BeginProlog
%%BeginResource: procset xpdf 3.00 0
%%Copyright: Copyright 1996-2011 Glyph & Cog, LLC
/xpdf 75 dict def xpdf begin
% PDF special state
/pdfDictSize 15 def
/pdfSetup {
  /setpagedevice where {
    pop 2 dict begin
      /Policies 1 dict dup begin /PageSize 6 def end def
      { /Duplex true def } if
    currentdict end setpagedevice
  } {
    pop
  } ifelse
} def
/pdfSetupPaper {
  % Change paper size, but only if different from previous paper size otherwise
  % duplex fails. PLRM specifies a tolerance of 5 pts when matching paper size
  % so we use the same when checking if the size changes.
  /setpagedevice where {
    pop currentpagedevice
    /PageSize known {
      2 copy
      currentpagedevice /PageSize get aload pop
      exch 4 1 roll
      sub abs 5 gt
      3 1 roll
      sub abs 5 gt
      or
    } {
      true
    } ifelse
    {
      2 array astore
      2 dict begin
        /PageSize exch def
        /ImagingBBox null def
      currentdict end
      setpagedevice
    } {
      pop pop
    } ifelse
  } {
    pop
  } ifelse
} def
/pdfStartPage {
  pdfDictSize dict begin
  /pdfFillCS [] def
  /pdfFillXform {} def
  /pdfStrokeCS [] def
  /pdfStrokeXform {} def
  /pdfFill [0] def
  /pdfStroke [0] def
  /pdfFillOP false def
  /pdfStrokeOP false def
  /pdfLastFill false def
  /pdfLastStroke false def
  /pdfTextMat [1 0 0 1 0 0] def
  /pdfFontSize 0 def
  /pdfCharSpacing 0 def
  /pdfTextRender 0 def
  /pdfPatternCS false def
  /pdfTextRise 0 def
  /pdfWordSpacing 0 def
  /pdfHorizScaling 1 def
  /pdfTextClipPath [] def
} def
/pdfEndPage { end } def
% PDF color state
/cs { /pdfFillXform exch def dup /pdfFillCS exch def
      setcolorspace } def
/CS { /pdfStrokeXform exch def dup /pdfStrokeCS exch def
      setcolorspace } def
/sc { pdfLastFill not { pdfFillCS setcolorspace } if
      dup /pdfFill exch def aload pop pdfFillXform setcolor
     /pdfLastFill true def /pdfLastStroke false def } def
/SC { pdfLastStroke not { pdfStrokeCS setcolorspace } if
      dup /pdfStroke exch def aload pop pdfStrokeXform setcolor
     /pdfLastStroke true def /pdfLastFill false def } def
/op { /pdfFillOP exch def
      pdfLastFill { pdfFillOP setoverprint } if } def
/OP { /pdfStrokeOP exch def
      pdfLastStroke { pdfStrokeOP setoverprint } if } def
/fCol {
  pdfLastFill not {
    pdfFillCS setcolorspace
    pdfFill aload pop pdfFillXform setcolor
    pdfFillOP setoverprint
    /pdfLastFill true def /pdfLastStroke false def
  } if
} def
/sCol {
  pdfLastStroke not {
    pdfStrokeCS setcolorspace
    pdfStroke aload pop pdfStrokeXform setcolor
    pdfStrokeOP setoverprint
    /pdfLastStroke true def /pdfLastFill false def
  } if
} def
% build a font
/pdfMakeFont {
  4 3 roll findfont
  4 2 roll matrix scale makefont
  dup length dict begin
    { 1 index /FID ne { def } { pop pop } ifelse } forall
    /Encoding exch def
    currentdict
  end
  definefont pop
} def
/pdfMakeFont16 {
  exch findfont
  dup length dict begin
    { 1 index /FID ne { def } { pop pop } ifelse } forall
    /WMode exch def
    currentdict
  end
  definefont pop
} def
% graphics state operators
/q { gsave pdfDictSize dict begin } def
/Q {
  end grestore
  /pdfLastFill where {
    pop
    pdfLastFill {
      pdfFillOP setoverprint
    } {
      pdfStrokeOP setoverprint
    } ifelse
  } if
} def
/cm { concat } def
/d { setdash } def
/i { setflat } def
/j { setlinejoin } def
/J { setlinecap } def
/M { setmiterlimit } def
/w { setlinewidth } def
% path segment operators
/m { moveto } def
/l { lineto } def
/c { curveto } def
/re { 4 2 roll moveto 1 index 0 rlineto 0 exch rlineto
      neg 0 rlineto closepath } def
/h { closepath } def
% path painting operators
/S { sCol stroke } def
/Sf { fCol stroke } def
/f { fCol fill } def
/f* { fCol eofill } def
% clipping operators
/W { clip newpath } def
/W* { eoclip newpath } def
/Ws { strokepath clip newpath } def
% text state operators
/Tc { /pdfCharSpacing exch def } def
/Tf { dup /pdfFontSize exch def
      dup pdfHorizScaling mul exch matrix scale
      pdfTextMat matrix concatmatrix dup 4 0 put dup 5 0 put
      exch findfont exch makefont setfont } def
/Tr { /pdfTextRender exch def } def
/Tp { /pdfPatternCS exch def } def
/Ts { /pdfTextRise exch def } def
/Tw { /pdfWordSpacing exch def } def
/Tz { /pdfHorizScaling exch def } def
% text positioning operators
/Td { pdfTextMat transform moveto } def
/Tm { /pdfTextMat exch def } def
% text string operators
/xyshow where {
  pop
  /xyshow2 {
    dup length array
    0 2 2 index length 1 sub {
      2 index 1 index 2 copy get 3 1 roll 1 add get
      pdfTextMat dtransform
      4 2 roll 2 copy 6 5 roll put 1 add 3 1 roll dup 4 2 roll put
    } for
    exch pop
    xyshow
  } def
}{
  /xyshow2 {
    currentfont /FontType get 0 eq {
      0 2 3 index length 1 sub {
        currentpoint 4 index 3 index 2 getinterval show moveto
        2 copy get 2 index 3 2 roll 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } {
      0 1 3 index length 1 sub {
        currentpoint 4 index 3 index 1 getinterval show moveto
        2 copy 2 mul get 2 index 3 2 roll 2 mul 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } ifelse
    pop pop
  } def
} ifelse
/cshow where {
  pop
  /xycp {
    0 3 2 roll
    {
      pop pop currentpoint 3 2 roll
      1 string dup 0 4 3 roll put false charpath moveto
      2 copy get 2 index 2 index 1 add get
      pdfTextMat dtransform rmoveto
      2 add
    } exch cshow
    pop pop
  } def
}{
  /xycp {
    currentfont /FontType get 0 eq {
      0 2 3 index length 1 sub {
        currentpoint 4 index 3 index 2 getinterval false charpath moveto
        2 copy get 2 index 3 2 roll 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } {
      0 1 3 index length 1 sub {
        currentpoint 4 index 3 index 1 getinterval false charpath moveto
        2 copy 2 mul get 2 index 3 2 roll 2 mul 1 add get
        pdfTextMat dtransform rmoveto
      } for
    } ifelse
    pop pop
  } def
} ifelse
/Tj {
  fCol
  0 pdfTextRise pdfTextMat dtransform rmoveto
  currentpoint 4 2 roll
  pdfTextRender 1 and 0 eq {
    2 copy xyshow2
  } if
  pdfTextRender 3 and dup 1 eq exch 2 eq or {
    3 index 3 index moveto
    2 copy
    currentfont /FontType get 3 eq { fCol } { sCol } ifelse
    xycp currentpoint stroke moveto
  } if
  pdfTextRender 4 and 0 ne {
    4 2 roll moveto xycp
    /pdfTextClipPath [ pdfTextClipPath aload pop
      {/moveto cvx}
      {/lineto cvx}
      {/curveto cvx}
      {/closepath cvx}
    pathforall ] def
    currentpoint newpath moveto
  } {
    pop pop pop pop
  } ifelse
  0 pdfTextRise neg pdfTextMat dtransform rmoveto
} def
/TJm { 0.001 mul pdfFontSize mul pdfHorizScaling mul neg 0
       pdfTextMat dtransform rmoveto } def
/TJmV { 0.001 mul pdfFontSize mul neg 0 exch
        pdfTextMat dtransform rmoveto } def
/Tclip { pdfTextClipPath cvx exec clip newpath
         /pdfTextClipPath [] def } def
/Tclip* { pdfTextClipPath cvx exec eoclip newpath
         /pdfTextClipPath [] def } def
% Level 2/3 image operators
/pdfImBuf 100 string def
/pdfImStr {
  2 copy exch length lt {
    2 copy get exch 1 add exch
  } {
    ()
  } ifelse
} def
/skipEOD {
  { currentfile pdfImBuf readline
    not { pop exit } if
    (%-EOD-) eq { exit } if } loop
} def
/pdfIm { image skipEOD } def
/pdfImM { fCol imagemask skipEOD } def
/pr { 2 index 2 index 3 2 roll putinterval 4 add } def
/pdfImClip {
  gsave
  0 2 4 index length 1 sub {
    dup 4 index exch 2 copy
    get 5 index div put
    1 add 3 index exch 2 copy
    get 3 index div put
  } for
  pop pop rectclip
} def
/pdfImClipEnd { grestore } def
% shading operators
/colordelta {
  false 0 1 3 index length 1 sub {
    dup 4 index exch get 3 index 3 2 roll get sub abs 0.004 gt {
      pop true
    } if
  } for
  exch pop exch pop
} def
/funcCol { func n array astore } def
/funcSH {
  dup 0 eq {
    true
  } {
    dup 6 eq {
      false
    } {
      4 index 4 index funcCol dup
      6 index 4 index funcCol dup
      3 1 roll colordelta 3 1 roll
      5 index 5 index funcCol dup
      3 1 roll colordelta 3 1 roll
      6 index 8 index funcCol dup
      3 1 roll colordelta 3 1 roll
      colordelta or or or
    } ifelse
  } ifelse
  {
    1 add
    4 index 3 index add 0.5 mul exch 4 index 3 index add 0.5 mul exch
    6 index 6 index 4 index 4 index 4 index funcSH
    2 index 6 index 6 index 4 index 4 index funcSH
    6 index 2 index 4 index 6 index 4 index funcSH
    5 3 roll 3 2 roll funcSH pop pop
  } {
    pop 3 index 2 index add 0.5 mul 3 index  2 index add 0.5 mul
    funcCol sc
    dup 4 index exch mat transform m
    3 index 3 index mat transform l
    1 index 3 index mat transform l
    mat transform l pop pop h f*
  } ifelse
} def
/axialCol {
  dup 0 lt {
    pop t0
  } {
    dup 1 gt {
      pop t1
    } {
      dt mul t0 add
    } ifelse
  } ifelse
  func n array astore
} def
/axialSH {
  dup 0 eq {
    true
  } {
    dup 8 eq {
      false
    } {
      2 index axialCol 2 index axialCol colordelta
    } ifelse
  } ifelse
  {
    1 add 3 1 roll 2 copy add 0.5 mul
    dup 4 3 roll exch 4 index axialSH
    exch 3 2 roll axialSH
  } {
    pop 2 copy add 0.5 mul
    axialCol sc
    exch dup dx mul x0 add exch dy mul y0 add
    3 2 roll dup dx mul x0 add exch dy mul y0 add
    dx abs dy abs ge {
      2 copy yMin sub dy mul dx div add yMin m
      yMax sub dy mul dx div add yMax l
      2 copy yMax sub dy mul dx div add yMax l
      yMin sub dy mul dx div add yMin l
      h f*
    } {
      exch 2 copy xMin sub dx mul dy div add xMin exch m
      xMax sub dx mul dy div add xMax exch l
      exch 2 copy xMax sub dx mul dy div add xMax exch l
      xMin sub dx mul dy div add xMin exch l
      h f*
    } ifelse
  } ifelse
} def
/radialCol {
  dup t0 lt {
    pop t0
  } {
    dup t1 gt {
      pop t1
    } if
  } ifelse
  func n array astore
} def
/radialSH {
  dup 0 eq {
    true
  } {
    dup 8 eq {
      false
    } {
      2 index dt mul t0 add radialCol
      2 index dt mul t0 add radialCol colordelta
    } ifelse
  } ifelse
  {
    1 add 3 1 roll 2 copy add 0.5 mul
    dup 4 3 roll exch 4 index radialSH
    exch 3 2 roll radialSH
  } {
    pop 2 copy add 0.5 mul dt mul t0 add
    radialCol sc
    encl {
      exch dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      0 360 arc h
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      360 0 arcn h f
    } {
      2 copy
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a1 a2 arcn
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a2 a1 arcn h
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a1 a2 arc
      dup dx mul x0 add exch dup dy mul y0 add exch dr mul r0 add
      a2 a1 arc h f
    } ifelse
  } ifelse
} def
end
%%EndResource
%%EndProlog
%%BeginSetup
xpdf begin
%%BeginResource: font YQYTWD+CMMI10
%!PS-AdobeFont-1.0: CMMI10 003.002
%%Title: CMMI10
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMMI10.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMMI10 known{/CMMI10 findfont dup/UniqueID known{dup
/UniqueID get 5087385 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /YQYTWD+CMMI10 def
/FontBBox {-32 -250 1048 750 }readonly def
/PaintType 0 def
/FontInfo 10 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMMI10.) readonly def
/FullName (CMMI10) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle -14.04 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
/ascent 750 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 65 /A put
dup 71 /G put
dup 80 /P put
dup 82 /R put
dup 83 /S put
dup 86 /V put
dup 97 /a put
dup 13 /gamma put
dup 58 /period put
dup 25 /pi put
dup 115 /s put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3c05ef98f858322dcea45e0874c5
45d25fe192539d9cda4baa46d9c431465e6abf4e4271f89eded7f37be4b31fb4
7934f62d1f46e8671f6290d6fff601d4937bf71c22d60fb800a15796421e3aa7
72c500501d8b10c0093f6467c553250f7c27b2c3d893772614a846374a85bc4e
bec0b0a89c4c161c3956ece25274b962c854e535f418279fe26d8f83e38c5c89
974e9a224b3cbef90a9277af10e0c7cac8dc11c41dc18b814a7682e5f0248674
11453bc81c443407af56dca20efc9fa776eb9a127b62471340eb64c5abdf2996
f8b24ef268e4f2eb5d212894c037686094668c31ec7af91d1170dc14429872a0
a3e68a64db9e871f03b7c73e93f77356c3996948c2deade21d6b4a87854b79da
d4c3d1e0fc754b97495bcfc684282c4d923dfeace4ec7db525bd8d76668602ba
27b09611e4452b169c29ea7d6683a2c6246c9ddcf62885d457325b389868bc54
3ea6dc3984ba80581133330d766998ae550e2fb5e7c707a559f67b7a34fea2f3
bebe4226da71af8b6e8d128c7ae0b3dc7c9aa4a1faef312fc9b46399b18c437a
776de1f67caf78e15d4cc76d6fa57dad7abc6d35ede0d7118e8c6f3a201f9ea9
eabf8a848d182eba8922addbe3c488f51eac02906400a84ea0abfaf48116cdc6
6fbc00330a76a8818cfaeb7afdeb029a204e0a70b47a05aa50153b56d2bf6736
c7a2c50b023ed92cfff13eba974f804a346d4130ccfd5233b6d6b92a14c87bbe
2ba216bae4123911e1856975e5cf4d94e44f400f687d2d13db288e0d821451c8
83e9928f8cbc41e0f4b99f8b29d3b11bd4ed0cbca83d81082e39a9e79cebf433
671b1af39c3d0e1f5bbe5f1fff62ff6f5f15f0421c56a4dffac682cb07b6f257
221fed1902e4b69d9bc2e061f2e96f5a46734f91298494a425ef6432f2b9778c
4ebbadd3483ef5447df5f008db9d91c559950ebcedb4b1316a5aae8367a80e06
bf3162beb99c4aaa617c60be688da7627f29c1775983ef635b26306a94f0b258
003779f8670a1398681953b785a226057f7d1270fe2dd2ea66d65e2061fbd65f
0ac51b6c347a56e9f3e86e52f3e0bf1d5f8d6540afb32a027a7c96919557692e
b739cc298ec7999b4286538edf7333cf8f8f6ba02c5e8c62929af07acbb90861
0bcb85345f4206e3ea130512dcfbc6cefa31ef2bd1da11d3010fec57b5b232ca
706f9c44fb9cab8903be783eca66d748b3fa5b1f5d5445f6c16a9a52c88a7e2f
2bfb0be4e416ea209a9810dd6c38e47a58dc9270b2f49f9b9d482156f7dc8164
b621b6803b6434a2a354a50fd9353a2ce3fa761423634b8f2adcd63b2b7acf15
07588caf127a0d6b2017a451d3df77c53e6171c66236e5318d49fab9ce4b1026
853f65d0d5f7913d88ea66b9b63cf06a4bfc8ed3246bb86cf6de255ff46d245d
109939e32dc483a0e5176b614ccb7f1adcf99854cf50317bd081131a146ea089
8ed59e46da7b6254bdccbc660686e2eda0ad7b894cd2eb2688c0c00aca589d39
e3caa6e0faf7eeb5df3e3f8113dae4b454a0d8c86fee52779ad3e13a0a871e9b
65b9ef0a2ff20989bae81d1cc1181679fbedb80e7d84a08774e6da58a283ba22
3780f2717484e066fa7dc012e6d19429b08638045352d358957917123c9c73b4
326a954f5ebce183ba1025c00c8f559dba85e07b3ed48d2fa0acafa9436d6fdf
e530ce25ac7da170db1764e77b6816343e8a128a075e7744a6f0406551f4640e
c403ea61696459d15ee040bfb53f08700c69333b1cb28142c5b9411d65fbfb1e
c7f4f50c03d122ad4b63e9e65f0a0af43efcc9fc546fd13da42a1c13b8c9cbfa
79a480d923701306249955ce1c61a680b2809d3551325a333a189db71bc83c59
47d17b31f8ff63564919b00336285f724d22f889748564808083ddaa4eeb8632
5d636961e1f634f3ff3def1dcd7299bb7679dbaf685e2ac1484bd9b17c5cf4d8
59897713b51a4deba3332c2ab5c48a76357d2eaaa539a617b09f223661bcb411
0e6559e99a7d900336a9327d4b8330ee5f56b016cebb8c07dbcc2fa736c07ecb
8930f26b429288c6fe6cee3e7792de58ea3ce248598db0c604787612bd137d80
e4462d249b229b62142128b57a6b44515262743bb3c70ee96aa4b8c49d6b0be4
4e19f634add30634f999f4dfb3dcff6a412a9b6067d28751aab1b20928a6e73b
cb81b0510d551f84437062e8cd403bf8c343003965e926465b288b0aa2fc85f9
90f9a63fce188d72008aed98bcba5ff4ae850711d2664f0857ded002e3a89fa8
75f930ddf7918d6b2f92ae26af35f50cc9d2a8f9b5d5d80981b12ddf4c59565a
aa62ec34589e5bcc3075cc6a163e45d46bb280b22158c5c04c90beb6f8a1c791
5597b0f69be3204d876cfa54481cc86ed2fe799bc46555c6c6fffc73854104dc
9c8a6f85331fce7c5d1f20af5d99e4e61b7ab981dd4eae26951a9447d5553140
b5862e2f39023bc7d14901eacf467a9424a6be8055d82f4b02036cd766367871
e0a01d09790ab2777db18248482fb32a25fadb62956b93affc59b1796f78d0b6
6aaeee9778a3b253bd98035c79b5296e173fba9e56e8824ab6191ef9062b1fc8
1b6b6185a05b167adccc6698b1801297d766492add5b66193d024d121633d329
25bcf1a9ae109371aaaeb64f2805bf5c2d5a218c191e9eeb4ac30a48291c7251
f690b51d5135f6a37f5418624c7d2f3ece356b12ec18f73d5177a24ffe371635
fc88231b3a95d72ca2555f164c503f91b5c7ca174e43aee6534df6d569efd50d
da3e950e11c6cff788e50ce5f1332ad76a2357c39d44ea38e88b24f2d37cf29e
21b7468adfcacc8ab8fe1ae9da4c933b5f7f0a6451964a4924b6ba96c359c828
d818166d5271e813f7a34a5b18927e66d61003392c96ab36b3e2175f31faa3d3
7e77200bbbeba91c532c053f318f3f83080bf3d641d4c5df796c2882e34c01b9
cf74bba01f03ef559012eeece809c019ab6d40d22a16fb9054143990db45b902
a5574f672dda96d6c18c0fb048e970e6180e6148061e22085c7aa4fdc2102fd2
d31e84456a56057b9d3189f331cc8354b195564cfdd23579574b7c7a80d2f3e3
97f07cdab67407a46a4264e985563dae7ad933dac054d64a7ebce65bb2beb5fe
d53360fd76a0fe706e7283550c4d5657aa9bf62ee713592d74e89998e9b0adb2
327a9dd5f19184a500870a3c53367431b56cc4dd60bb629ae68a009fba0049eb
16d11d5f299d5a99f3d45f6510450e53740da5556335eccd43e1408b826fc535
10c7784c44cdbf41988ab67ffdc54ea61dd05208204c8bed9c66c678e6324428
9682cc6ea0b2dad69cdb69dc8daacfd1a98c730dc3d9bc8d83e2fa2e72de08b0
031ef3455ba92d03acfdb7ecf50ee883a8817abd96e58f72ae050feae0d224a5
42aa0b4c022f8a90e73ab84216f520d6ded72680471b9ed2ce317536305d7360
810a92f4957c9aba9328b116349fdfa728e9f042b2fd2d116bbcbbb99ec6966b
a5e1f4fbbb4b1eae6d8bdd40de5fa44127e6d7c05abad3c012082c245265096d
d4445b03ad8dc08d707ecbf0aef0890b0658dc9341fd386d417ad9f5e79c0464
be4e3b22e4997e1806d192a8be70dfbcf69715b8194347a60e80934ed09fb08e
c4df7c3b204b07ee3610c041dff7d4c76060e4be6a3a2f0b0217005ab38f80ff
fe55a6252afa361b5cd8f3b642e6e193da913ccaeae5508c2470036aad80c0c6
e977c374852b69a8de69aea44aaad49eb7fcd420bd55a5c5cbf073e859ba9d6a
857da20a5cc2744843ea07efcaf91e992f0a44e1e520bbca097b6965c4e30c99
03ac3ca1af1bbeeacffd7cc22e7b9763b0876cf8308ea38828a716da7f430898
2beecd1cb81cd95ab8fe70242026f11061a70fb42445aa9246488d6d0029df17
dea43305ac74df52e5699b6c243025786b21fd43993a8039e9e75fce2dbb7d6b
7e4cd140e7edacc20dcb473dc45eab68d8ea296baf9bb969093862d391f84073
5e17f87847ff2e9186080feb184ff7869a5a8bee6aafe3461454dcbcd00d2c24
61ef831a52dbb0fa736694b4a3a4d85c6d80636b316fb12be67f0887cce6df04
80c145ea8762ef8b2c43ae71f3c32686fd5813eb49a39bc6d4980472bd5cdbb6
c282c9ffe2fb52656f607692e1ba726417703feccfd4aeaf9c66d543ce1506b1
a9d6b95705f67086d4f36b06a283cec841a01f1028d95d4de419d7110f091014
f6dc905e81add1d54f95b16cddcfd0793d1cf4a85e7a35458c81197a24fe82cb
63edde30cb6b538a708fbd41f00268a772730b85bd8860054acd93fe6b8bbcb9
cc474568d426e83f15838520a313e0ae1b60959de340398b21986f5c404c9361
54975d52740bec0f7abfaf271a2ac1f7553b862d45d11ae585936fbb5462e2dd
bf35e4afb7bffcbd3294be3eabec4b787133c3a5e0c95f74a71dad9be990d07c
d157d7258830a3cc3de6459140afba942eef325ee072b3a53a9f281d483eac65
e8da50ccddb3d43baff7d8c7d7a1847d6d579ce92df1b54de141ce7a73607362
7d909e8cd9fdc373b840145f9373bc2f02979ee34688bf840f4f9245c2ab976c
ee8bde685c47606201f6611e38a49ab72428def2c85e553313af719ab4d4f5ef
e3f3430522abff76bf8bb8f56afe11008d3f989ffadccb411dd3b7e6352ea873
3abe5dc71b3b4832ae85bdb23f6cbfb4b2631412e4fe0050a5f7f4216508a3db
ea2d74318ed82f1a2fc791623c869593dcfd6bfb2fe57bdf06e9d1946f9bcea0
13848fcdc603e3eca5384725118970cebcc9ebc6b74df13ad395fa6efdc22463
5380eb1b3521aa929eba30958ae2da40852196b67ee44409d323383b0c7fa1f2
b4fff373041d9f5eeab03d6743f0a291b481dd3ff9e8ebd77a073b8d5f5d93bc
727e6566204893af892f74fc0bc3f3e83643a93747678eb998f9c91b3a0ff942
3d3924f507f1c7eb18249b2ab73691f5fac868720ff52183091f65ac3be8cb0e
80d257c52ea8647ef747fe304598e1ce0900a4de4031e4b6a58d7869b08a56aa
710c91ccb8afab94ad10d670e767a44e0177795ddfd65c9cdc7332716deefe3f
9e2ed8a54bb6faf63b7bf5f554b934821086c09fc28fa74ea2efd410e006be6b
ebe0c464e078c14968453dc783a788a55d925d72205492c07d0dbaee4982fbed
9b32dd19ae230da5870499feeac55b09b0970ad5926375fd79b95552816be003
90515262b5ca891babcd81bf86847cbc5850d4a056bdc528e97aded1ea6d7b76
bd8ec34e742a9fccf19a6310004499b1cc1a920b5f3b746bd4de2d9b9dea341d
25a7a7b60546a8f9ef99190cf8ddedb21a0103414f9f28ae8673c966b12528dc
fb70ce44db4822322605982d708a0b4bef7eb08962e3f433213d7545f351e994
970828eb443c3bb36ab0c4cab7fadfd949e5f93273141da2b6dffb41b4678647
93cd4e53c78a63c632d4fcbad772122e86dde337d5438e5e4342a0e18be8b014
3ddd7290d16096f2149c6c71ad28325dddbf994e651b9d4be89430b31dec3fa7
d2703196f7f10b5e8d98f20e14151160507e53ff1f3d4bddff3f45f9e64b1b9b
9b26b32bf389a3725c243209245bd78c2f78d67033be00ebe25955a1ac718305
b52a0260a07220a9f7410bad935538c6c7c56f902a70730c1cf90d45a5f66c6b
a762406e512bf3cc3b52918c6e9e92893279cf86af1684d9b67d1ebbe84be9d8
4b56548323ab381ae18c9e9570453abe77ca9d9ed1164563120b939fc3acc33d
49f5e989a74ac760f0c99458295278efde92e99003c4780935d12eda68a82308
ba444819ea9fd930c80263b57ec1b9164aa50ce386b8ef81a53a710416c6c868
794bddb4fe463b3c59ff9fd085fc7ec37cf2abb7df09d41113f4542f72bffda6
1fafef41c462eabcc7a3b4fbe46cac256c7af4309a617e73e7934450434e344b
5cb6ddf2e63f4523f1526ed2f79522eae16b23dd9ff4924053a0fa7c4a0b29ff
f4485c041b06147d2c94d276553f443c2980cb96ef5da49bfda4ee95bbf092ac
e2dee947d0c711c1930500b79a5424e8494df6e1798b009a3816342f4d1d7cb0
b7bf239f3d60361ac605020591740d13ce386bca1e69a2e8063c62f9959c9fb9
010ae39f18882b1e3b3d0d9b0447db7f7f7a3810375372702686b224896bf5e4
cd40e308b5a6988b614d8088c296171423cab2657cfb98f462afe21e990b0c74
4c8738d1b13097ca887ccfd3eabe4f1e29df71d0e51046957409964f9f02a33d
78b2a5bac5058bda0dd8a65fe6c53dff9310fd2b97afd24f39e586417dcc18a1
5c0be1795e0f2c3d785f8cc1ab5505bb8fc0dfa1364f08876a42dae3383f853f
84e7e54405bb8d00911c5b8ef4794494d9bf076d57a65f2392628b61ff967c77
29114960e00fadc36961617c61c673bd2d2e4a9d54702233c8414026e67940bd
ed16e2d3822f06068502c0966f2ff68f74d11a0b780b95f3f52bcc162a37b6ef
48cf5ff8513cf4183176734f80b9835401b3db6bd53597645873fa96488eb183
646b577037e5717952d23cc71ee1780b3df42d9c768804fc47cf147db059b9ee
7a6399d4f4afcf2d296902f16d56d6df28ac4c9a96e357678ba901fe72ce3d2f
b10fbf263146547d455df1bc33a1dfa753251c264db8798da35943a4940962f9
e3b8a68d2b094177154ba30af7bd201cad919c09a34536e41d6c5772873c0634
fef84dca5f1a5d5488997e279876af1dfb3f51790a6ae085d09ea4e1947fc10b
987c2db0634c100484f4b45404119fee7a7ec81111029cff1b4cfa1a8637d4a5
ad472b5ac0cb9f428cb1df8abfea3db8082a26cc815437ab387e7f87902398d2
e0c6bf6c95c2381f15b61fb2c5bdb8684afbb7a6c1a01ca2286a8dff62e52a16
3d7c748c1b2c63d2933012c5306cb7efb0b4cd733c56ba7700acc731d294f7a1
1f2a1f8f461983f2972da8c3dbb3f9117f7a6f3583c8a5dcabb364ac0310457f
93fbca26c31482d806c6a7a4f87f4cb92e3f30b4dd2dd5e3da5360430c008237
7165549aa416a73c62a50b707074b2b7ded2b07454574f60861cd2f0342e4f78
24789278e711f18ef858b819a0accb67384b47145fee30b32181d66ff47aa657
83f0cccb693ac70657bc2bf204974bb3bcbffcd6540477e7a973718754acbe68
823672daeaf24c93263a57598ac4bc999120e367aaa4b54c643e8c8987024b07
9b0d40fb33d55cee534e3a38a1a316276704e9a6df08553fde29e4d4526225d1
fbda6f8cb78098e83e8a360de3c4c77e2998094f920aaba9c7587735cd2f22cb
e17c6b99a8286519242f18de4aabbe470bb8e0931ec7f5c19e1c304df56f2368
70d154e925c4f2e5012d52a0283ea52acefa09d2a8ecc832358868bce8efba7c
492e3575c1605150a3f7d6822960f1a9975151c7b6e928fc07f73493351895b3
5ea783de8482144ddfaf6f881d0835472a603fcd52464da80de0c380fed5cc67
e38eea70c066dadf026e03fe00be35c6310f64aca4b991ed4bc4eb125b4c0a79
b87109b442c0b624c340271988ca36e92157ebe00ace90fa4515b6c649b9ef36
f82cfb4954c124878dfece799bd987ee930148967069b9e6ff5663689e5d186c
26dbdfa146c3dd3ab9c2104fa4e92423c88a0821443aa8008b11008525290207
146118e39b4d7893fdc8c7225f4c97fa3f1cc264122afa3a87d630ef325d3778
28ecba34700bae5038bc2a1c2e0476351d9e73cb623cf58eb35d4c518630ef2a
f8b64bed95d72bb7403e652e2dda6faad38fe8fe4319ae190f0496a1c6806cca
10efc6d15c7e19522b152476c36f9644a599da6786df08fe7981f9eaa0e8611c
1d3773b2c6291663f0ee156b310e2ba3a42ec1fdf11ec8bda99bf88d2316c740
1663a34cab0c691b6ac03b4eb083e8e043427c28a2c0c9afe2b749b8d34c34ad
b130c7fac6bc26dc1b8fa3fe1462e6f344c1bcb311128b7fef549e33bfb5b81a
fc43e9a3003c3d0c44b467bf7df140bd3fab47d4bf85ffa623e6d3b4cff4cd3f
cb4806bb5d4b098f3cc567e9da9952f5f95048b505dd58cf609e2f9d944edb02
f6b959dfba02a986463f09d933d7b3fc7ee6a88a4f515aad8b0ecbf97ac6ed27
2bbcfae1bc994fe5223c239616b2b23a8186a8f4c76c77670fbd4bd65f5eed52
68258c037ce974501e9d4c5cafa853d441e20b4613d932fb941f118ffd512fb3
560ffa1e35f8249d0a8f141a95222394672b524a6d6d924cfc4511b35eda4b5d
0e805183d2990cc5130ec9f6deae9a3eda3632ae2e6a11b35fbb619fed16d0ee
775801160ddc1ae68948c2eb43277bf542e28304ae29f30e5d3aa3f2b83445b0
d883e9bdb962dba6fd1d9ac98c49e358198d4689d4344ef74de18d70f0a0e26c
d5110b932542fc982d4007668feb42c8ebd9b164fc63b71de2cc1967a1b283eb
5146987aa44cd3604f4da0c8d4ad56efa9fb157871f1013b8669e0e9fb79abb7
1f30161f7ed5e4ecf1bae7818ed4c8a345f012eaee24d3338e737ed91b0ae2aa
ceb599efdbd30eb0775354b9f9e9f960979e6bf081f31a128f9eb02cdec0e817
e1dddf1dc6df77d48c4f103d642736cd77c2db09ac21af3c8984b6300674a2ae
abd3442ee0935cfb511469469471f02429f0dcf8105bec744b08a213f434300c
a0f586ce9dce2927bd0ad3c842c439b98d1f5e6c8aa3df39950b1c358c9af731
6ce075019754d92ab88a1a9df0077bad2415f5e7a649792dc05cc9fe8d9ad16d
eeab788aafaf232706a59423d7427936b908601d8a03834baf2a567d161435b5
52e5720471bbd413a3d77a4dd56eb3ae461edb7cc7013d8a5fd540815c9fb3b6
5d3bb3d5a601ef4395b91c142965ab6a4199fb03499757f0f68668650a214c10
1eac3637b3900c5c2f6f554fee41e36898c70c6cd6009619ce188579b08d6dc9
80be12f2656a240f376bb0f2e2871a1bd7c270309c0d9c2ebf067f281168492b
cc7801565761da705cf60027620248e255842a174041c9cc4e1faa072b61059d
e31789ba0c3710083422e5d8ab97d5a38fa273b0d4e611c4417e629c3e671688
02de0fc99b4be7006f4e68fed42b8ca3852d07c38bf1a1b96a5b5a64776384ab
6fd5a394d9447fceb1af6d469f5a32c06a2b40e2406da2b6b0eae8b4e9528324
8b42fc72deb632732286c17218a1c343c2bcf2fc42dc8abe2c250024a183e688
67600d3a48c669e0f598ed95317dd5a2fb3ff4c42019a0f4952c66ebd80faecf
7e36cebac47c2bf13d47bc9efc03fb84e953dd050d05a6b057681d0b7e0883cd
e4a8ea7df485266673f31eb03888c4351943adf37537b3b362a3d16c4c14fbd3
7797a63a93f7ae7ccd11b766a63c991229d539fa82ad3108368cb6d8e1931110
c8cc11e0701e3a70c992ab74a4e8334b91c05d4019de00b26b4d00f4dc785a95
a80803a6ec6480eb4d2b257db355bed7d346472bcff9d49fcb7d00d0839f8f6a
4e038e6255d60ee3e5cd95513e24b8a5c7adbb56b77dd08c0131165d2fc26357
a202af38f951c3f337fab4c7fcff0b3105a79a6799ff7066b5e59d3caa12c0b5
f0ef1be138cf26f1cc879e7ad6772e73dcecbe0d0acc0d497ee654cd6cf858b9
f641f48837f61b054494c361de9f2e1388d05ae4623e944ca603f0ed3dce0bdd
d9675644fcba71a5218d6e1d665b5eb185dc091d4e20e7894e935ab52cb4f554
37984b6187116ebe33dce15360a9172cb4a3f755a0ec445ef335bd3fa097b3b1
6d8438d0d6d74b9f5012aae2ac03aa60d149c194b264ac3b12ba96f806be7c3d
273168063f81683b09a37efe85e40db655d5550e707ea238ed03cd9fd4ea3dff
6333593140c974174c829558916efc2568cabf4efc25ed281e23b5f9b9ca862b
e8fdd5c7e299596e654665a84c7a3a7dd10200b78499f7636347fbbe09804f9e
24e6ed9bd2dee3a3a1350b375c0b2d9e69a12e1056fcc5f0302b5428db9bb952
399d5b5e5a7a41973e1e2baded98ab8dbc7c0a6d9f0f64106bdbbdce75b8fec0
c889c835d5a5d63e9df837ae4d527f84caeb9f92630b8a71b30eac3023dd0fd0
8ce556130e32e9e773298e498ebae3dcba9b94e3673dcefdd622660cec55faf1
cdc3220e7a352ea40fdd4d085c74f0277882454380babca245c13741e63801b5
ca823ecab1b1a94642797a07e15025fd436a72bc6c40056735c60264ca3155dd
bc936d7c070784a30e1b8f22eb8889dbb17846b1eeb0566b08038a7077bdd2b1
f9765ee36bce2f06689be3945a8f78932220b3c3adbbd3faf5b4bbec541650a6
e0d3d48752e24602bf372e718822818bf3ffb976caa33f9684ff248eb0d669ab
9a3e5c2d85f37ee15ccd2b271427eff21d18ce222ff3477c5c223e837498c62f
0fc7255c10543711e6579f391f8aa341a658ca7126aa2239195e42369d2ac8c0
63e1fd8b0f91b6102c6f97f5026ec18b483edf73ddab865f76459f2268f775a4
46dc4d396ce48d2b77f3c4c274d231b028324d9608cadefcad9c4bd0648264f1
cf2a7ee66c5a650101d0b0943b495cd44bf64a9a9b22d19c18e137c15a2fc411
df931690ed4e3dca7b841c7bf41a2f0dce99a059ee3c3c821ebecbf3d51fbdba
c970a4765b92f5a6293dd8fa2cf2b25e0001afbecd291de70e5d9f1511dd6346
9f1567c4749dba82c76c40192af64f0746da17f459cf200674f1164b70868761
08aa87d78e967b973dc20d1a8bc936ba6ee3ae344f9d18b4badfdca809f1bdf2
73682c763ef5b5945c42ab06afed4b33f3ca014bb0d330acfd3548fdeb6bac08
b9870b902dc5018a3dc8e00587db6ca31810d3f837cddbb2ef1c976fbadf144b
db32805ef4cc6f6b1f3141fa313acc5c6658ed248cc9b77053a67b926cd92fb8
7cdbf070ef4bd5a463dcc84e2e6fe78c4f1cce2415e4cbcfe95d5a115801599f
79773a267de8b8b75db241d216a3c80bdfe6122d61a83ede4865d3e6be0dbcfc
ba69be73828cf1292e0ce8747ab06b17d1dcbaf44d2036536c411db0dd2b7a20
4c9557008f7377b324c4b49872566677458f7d87372482c25e672a058f976821
57bb9a5bf95fe43e993f3b3137345c9a7d42528690079e824af45a317f213c32
ac83df6d4e53f991e7c4b4f2951675eb53fc4dfdbc9af4b7c1526345c4ffde6e
6689b473c97fc93afcfbce43463f1ea63705479eedf87f3747950189833a46ef
411f9c68e287501b559d91ff1490b0d77c67bac9131789798510d026b4777ade
eecd205f92159a69ff78bec0c925dd855b3d962304c0089a9deb5315c89c61eb
73c7e8288ba0baa9774b5f4a08a2c8c00d5a6a3bf016630650b949727375f1a8
c891859933377251eed80b737ab9189fa931ca351c8439e496351a11992d8b3a
3ddf6387e4d8cb0547756effd17592bbcdb97e8fcbb0da3d41d6c6a12feb7313
1c530c8331b25749ed4768a496b35faf813edf8e12a81696c045
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F4_0 /YQYTWD+CMMI10 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/gamma/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/pi/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/period/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/A/.notdef/.notdef/.notdef/.notdef/.notdef/G
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /P/.notdef/R/S/.notdef/.notdef/V/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/a/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/s/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font SOSTRQ+CMR10
%!PS-AdobeFont-1.0: CMR10 003.002
%%Title: CMR10
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMR10.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMR10 known{/CMR10 findfont dup/UniqueID known{dup
/UniqueID get 5000793 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /SOSTRQ+CMR10 def
/FontBBox {-40 -250 1009 750 }readonly def
/PaintType 0 def
/FontInfo 9 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMR10.) readonly def
/FullName (CMR10) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle 0 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 91 /bracketleft put
dup 93 /bracketright put
dup 61 /equal put
dup 40 /parenleft put
dup 41 /parenright put
dup 43 /plus put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3dd325e55798292d7bd972bd75fa
0e079529af9c82df72f64195c9c210dce34528f540da1ffd7bebb9b40787ba93
51bbfb7cfc5f9152d1e5bb0ad8d016c6cfa4eb41b3c51d091c2d5440e67cfd71
7c56816b03b901bf4a25a07175380e50a213f877c44778b3c5aadbcc86d6e551
e6af364b0bfcaad22d8d558c5c81a7d425a1629dd5182206742d1d082a12f078
0fd4f5f6d3129fcfff1f4a912b0a7dec8d33a57b5ae0328ef9d57addac543273
c01924195a181d03f512ccd1267b42e8964a17d77ba8a5dcc6d878b93ca51f9f
0d2c97dc2d102ee8329baf69528b6eb7c3b176ccd9be31e4a0952084271bc613
e493b1a9b7145f72224f15afbb5f8b1374b1336b651de8be6642ddbcf656c166
6a971cda39d2b3ff20d40d5968eb80b8c17bfbb471ddc9cac62df78697baf8c9
b7cae3c17d57a73fc53f1c6777312a45685b8adcdb3a9b1d9705aa74cd02c057
654914102cda769538fc0561853c7b82f142fa1a31e2a430305a3805c301cc1c
ee35a07cf18e7dadb5f04ebee0d411d76c77125d83ff83364eff62bf97f0f0a4
19683345609c8628a19b45c189a1de8f27513bb265b5d483aa2ff0e0ad162e44
a9791f4c92e235d8f1c724a5344947c3e5d7aec98a5c82796af939a32eee56ad
55bb9035a35121e4ec8b2dcde8b581c8428385c439f664e8e2f6abab425e15e9
6f56f9f0ad778842c98ee1543784a189be52809fc0734f9947418b02a6f7e3d5
c3096223ed544276216db78f0f57543dfae3cdc0a6fc772caa49442527a5d94d
c54be93c877cd95dd844a5c319b080401689f5b78032b2bd4ff828000c9c10dd
8e259ce6db03235fbdc9b756f1fe1a421b5354f8a2237ae000c3d7d2cde321cb
d1e3247b6cad5ca734c4b8203b358c99036c912621d7e3809af3df3d288c8afe
668ab8de557741b4da1cb19bd4c665dfecc8cc04422307bd3330143eceec4820
a4a9279cde4ca52b14ffd6939e6ae27a9d40fa1f8fb83dae735cb2de14f53c85
ab3d5cc0590124df443f8855ea09d0e6fc36959fd27847a1516ec7ab1b9a8a19
e469af25d6949e21d7d10a4c320017b15b9e9a11f4e3a57f29218c6685588208
63e8118b0800e33cd52714c8b28f96f15213503345a121842d3ab1112711e0fe
d0410e4a0faf2e05d9c4b2434ace004a74aa0026c37b37069036b10a238156d0
c3d0c0ebd5d648d51b93f38b2fa9ca0e46d76777224635948f77f15388247caf
ff816f513ccee7ce970b0bd1607eb63c9d1e3130a97c0899ff3cbbe96defb4b7
f9d89cdec968f0dea084dfade98008b5b5b0b09b3fc919603ff33796eb160b5f
cca0055b95bef33878503c3431d51df33d74cff84800da0f0d3b3699b9b87d72
4b7531e933fb9a55430005699a16b44874adb2d1d37df679181ed6fe7e631e25
5cdf71ef805cbabae6344f3476215b9b5ff749baa2b0efb3affc15c6e6638b1a
30df1dabf24d4af94d9f5930accc8f767b36df1894d65cf8c32002729f71c99a
2233193df703949d54d2594b2edc4b18eac929c12c1747ca4b7b6188435a4247
9ebd0a1e1d79db280e8a4b2786c3324f30d35697ae36495024246cfbe9faacb8
2d9317e05bc018ebd465cdc98bf8c71a08194bccd7263225679462af7a87f74a
cc19992c756f7e4dac32c4187ade759299a087d4362a9abb2aa60dc5c20dabd1
ff39bfcea8df3fc4a34b9416632918cbcff7e15cf0679f74ad263fa9e38ecfc4
f4fb6e0654eb77bd93e6bc24a0644e5c43b89ba4ceda4ff6d6cf40a55732781f
e83871214c64d2aee31b6feb7ee431562f8cc8423d40b1f4faed213092c159a1
6f7af924edf9d0f7c78025c4adbfd1c91577e1dee1325d6faac3df20ae5ffd3f
4968cb0f75e8a1426dee4606173ab5310e08d8966408a9c87936f782c0dade20
1d460da884184c6e3553f27726a92debd3b0af9e477af8a839ea183dc82792e4
28ccfdbc49fc684efab4d67be44f12200e9831034c7663d56d150569b5a6c026
c8224decea6dc440b757d586ad18a4ad6ddc622530d998052afa609aeb07c4a1
93df932f66f5c39d6cbd25504532a13a1e56412953424c2fe63caa16ee3513aa
439e41a3dff79d6c3bae7bcbc00b2823bad858056e46069222088b0098008438
7b52d86f9211c1c4541728e45f57f0026241fe7f4b7c6f4d0b5f13d6d3975711
dffe1c91bd0d79e44de8ff3680aba0b15ebdf761749e1f08404f31eba12f9d00
46f11f94b633791e2399e3630f4d4dd7d047c55afddd5b036dacffba7acf8c46
7f0609126caaf9ab22c24a3eae6504d856428f57421c7de756299004dc53c8db
69192ca1ef81dea7ef521216b816a5bdbb468dc703aabd509d2ee8bd4c04d180
78f804a6185f5bce5856881117c7f3f451a0af0d5450fff57683a0f90a65ca2c
9270feda1a83727f6893fab8937516f190848c602b6c7b1a08f76551f7d6905f
40661736331a48df506176d17a1955cd155fb09fcd14c65aab311e2aaae4c78d
12af8f4d2bc7627080863b7bddaacc0981ad513316e856563bd8a1bccd88d30e
0d12ae4f2e4f9ee0692cbc3838abd61e83ecc38685679f3d5c3de0402246e0fa
4b46f854a162fb9891be56818e6c286c67aec19dda62d2ad8ddd21b8e8aad596
d5cb5ce1fdf96134513117b0cc7e20ab39e27156a5b8a7cca52092735e6beda2
73648e9b6e0e7a91c10807ada3e7a43ad61c4c9e7a195d8e11f0aa720b8aa5a2
aa83764e44be8b4d47373924494c69fe269341d8671be16e6c367901874a098f
464fb5f23c4b09e5eb50cda44f8e414118ca7686937fded26ca226e7b5f859e5
d7b427d9ce0057dad0e58326c0a230814b20fe19159a2f690969d9d27509629e
1ac2430a38c7c47a4148a5d59f33010a792ef25ba078b9e2dd74314175adaa9d
0c7041cf2e5b34a353d8326277942b632074a9a4ee4e651a18681c44ccb2dd0b
c52299211e7ee4ab3b2b37705ca47778191259e2470a5edd3545aecddce89315
121c9f5fdcb99647b5f7e1f0e980281e410c6cb713d1ee3160dc38752ef3752b
eee3d922faf33e3bf02c7f7ac9b4d1250a6fbbafdfa07803c83098738211d6c8
191257314678cfeed4e897df2067fe6d918db5785679f5b5da11d19d225d237a
7e1897a77076f2c10d9d1d869199f6d8c5a82e7242398924156eb85943ad4331
fac474aa644023f7a83800d06b4e87d48b4bb001a0d33ba3c0ead4936c8146fa
28060bd88c4ef38aa6013be0e1a564feacc2fbed0192ad10fcdf2abc8a3cc6a6
a195e3c5138413aa0373c0a6393cb5478f0d4345608556e9a268e0bdc9c42515
5193ce46a56f50bdc4e2d111837f24aa90bd22d13333bcf75039d739ec5a8d73
3987012760e3ad1e0dec72da57f93a4e94a5ecc873d3f5c794b71f400666830c
9c5e1d57dd852632347712a96c7a0be624d43257ef13b277dd85c6ec4f3962ff
a3e5224fa69f13cacd57c32a46125ddd2fa66079aa8c51b10988c9945c5195c2
1b462aaadc695416f18de85e4e20f6645fa34d6083a486532554b34eba4b378f
af082b5299d6ec5b72a59bfcc859f5c513ed5971657dbcb1d81c0ca58bf7d859
8750faf40ace46015545a2ecf3fe8cf0d34b83c0d50f488c27b2b53e015a5140
ce0f49d9e07425a3e4ff969cc05ba82937c426befca068ce6e9d0cb119e95927
d4db61c2b654c3f12758727fd4df992f6e5f6e95034a4ca1160b082896400ab2
e7a0cbd09a0aadb54e1d7b4b46b5dfdbf05e6b9b62dec26eea7e16ed604cafa3
5d08db61a455a101b9c57bfc881276e2ef4cdfdcbae6a23493f43198247f1372
6d41ffee739514c2c6f3f26e5adf032a99bb3da9f7ca73f5f06f9b1462407b91
79d60b082143431f8b7b1763082e577f5ab6ecef1ee630176e0be06270856773
509864242dd15cf6afced49b264c3c70bf0412b80f6c130c7cb97e9bb438e8fa
2ec9c496b62b66cec77a79a876831fe15fb2427aaeca879f86f4323f76d4bc08
0602eaf3bcf5d787c3580161a3213819d5a46d0a96db87186777d921070a08f8
37e54609594079535d7ef1859f0299adf96c6f42d6e9ac93091f969d762130f9
e8b78a4694820cdddffaeea945df615b888266f8507834804885a0157cea0757
fcb43bdb471ed614105913223342f435d9f3fce6f8e1485c22d3ab5b06f83196
ce99ed63354ef839aa703e32374abb42fdf3b5732f03ee8ab66728f4a9781551
2c0e743e5baee238cd934773c5b8813a1f5224395d36142688fa6d79ae2969b5
198a76c9e96ac2f657a88b4cc452425e1d5242616cbfeb78b35fa0d7599d3ab2
354da7af04dfe6eedb14ef8a07138ebbad0fb51b7fa8fb2f6aa485e0c5d9a121
7dde6094eeeb4426571c80c8aae4d65158b9240648dfa7e70fcc7449a4adbc09
7fc8d52ed9591cf140d86e15ab7296105ff4ec6edc81c2080dbe4ffce374414e
052d4c0d6e968b973f055fde165e5f85db671492b57e9e16c68f3b8d601eb0d0
eda84b4287def03665c4b6c1dc1faf91b80a3e94e86cbf517091861aaba27fd3
29c086b69df9b5a5f22f8d3b075319270c5eb9f53ae474044ab16a40ea1478ab
b38345283047ca3bceba15db5171028ea9c7946b5427b9f09e103b9e3c90711b
6ed8e47581746c4c43319358c42035cd1a970a7191d7c471d2a5813fe48bd07a
3143532bc01ca35031c37e1e65c9025332cd0b33ab4a964ddaca84956c28f1d3
b524081eba65c951e52f6d704e354b370157fd658a7c29c3dbd8de618a4896ad
e05ab9d3af34758d557dbfc5c4e7c3f4a806145520d121cb965995ecea00f921
d4014908d459e5a8d39f194b25e863a545afb8ec1efb9b3d42d9cc495d1b8053
0631f72023f3d3ba11680ecc5b51864c68aa592de5827e5372fe796135204d50
5947a9d5d03b1e39048d1c5d04a9d1175900168b8540358092dddfd1281a0af8
9c913e0b9dc383b7c944486a87a210e3731572158278dc960ae62ec23edad0d6
afafa1cf6b97aeda6cc43b2696af233ce7da9ab0f265902966d1e4467a9b60b7
c7b73fa2e349630040534826963cff05bc92ee0465766e003813819d46821c5c
e356b1aa33c5f361ad41217979bce33af1d32b149e6321a378f005968262cf4d
fed689e12f667d33df969bebcba6c7e32247a99611ade727664d73d107d41f58
5755fd7dfcf6b5b7b859c4b58d5e0b80d4d7256acdc72148beef8b4f48ff08c9
cd8e1f5ff9b68b3be887b2cef27f91e24ab876a10eb2815ddc230a24d907aa0f
db2743683f8135993c845318fd1dbbedcbb0c1f14093ad189d099a61acb4802d
1499417f638a86e96c6f5701b44d28f28f067200b7a723db60d7d06e597b6adb
60337c6c02761dae60ba27496ca0fd7fe0b121e5b4fca1f5d350c2caec7b94a2
0645af98ef3dce7061e85e0b81d868eb4f6b03609db7ee9be370f8fa0cad3875
79dc2472f296ddf395750a667d6371c32b35c1797e21fddd5dd59dfa1bf8c0ec
0e552cad01be74a029e6693a48f2a0be4f85c4db28ae5f654f81e91d4656befe
71d006163eac75e8e0c42d473a88e1f1c47a839e859b485a5c258f55ed76d8c0
001e0dd07ae35e18e0cb428d7925804e54e2b8b6333d18ae58ebe03fbc6d144a
92f8162dd33384f71d69e3d74840dc908166cf83fd6bb8522eeb9bf5fd762780
c76d2e1227cd53e3c244bbccd96c79fc1f18379316a20c59f5d643b3adc56de9
b55eb6af4775355f479b07f8b5d931a6fb0f742f8cd40bfee08dcce2f00ae034
89b131ad6e885ffb443e7d70062be666aa673968241dfaa8c5015d40ef4df960
d85ed2b9474bf63b35ab06a477c7ebbb04e4497271ef41a833664182df591169
75ac80c2dde4c3f2bdd1efecd212597210e91d44f5f63a8f8dda641e0752a503
dd20934174110ceb2daa902c1429e2ba61aaa4c9ba68e2cf395bd4a775ff0853
e718394b92198411c4544ba9615824e47767c993b64f835be202788b1b71c783
a37904492896ffbc6a10354ca7aa49c063b57d7c681ec024917a44e21355cfc2
9077bb598d2bbdfdac5a3aceefe7c4cfa4c59c31bff2b56c7fd965c01bc70160
75f840021a7c04acec1f15d6dc88e8b49ac65eda361bee2f9e79d1fb6061f0a1
12a6c80d8a5bafce8a1060d2becc459ea3c2771ac105ec611e1b0ca17ae669f2
4c618417127d6acab0e7c940fba38ae57dc57f780fe6ef57b6050799e56e8773
8e98306e2a0e7b0eaf6c3f5aa97af38b95ca128b3eb8e738ed1f702d4cd126c8
a3fb03ef4b603e2060b4a825c26096a2eeddbfc973aa3fba76cbbbc65e5cfc89
2a9215d6fd51cae1a84e6266852bdbbcbede849e6f22098dd9a75509bc7ad1f3
67ea67cd61e48e9075b446a0d1993cc31358fa79ddb8aaacd002fa2abc02c867
f6ff343f58325dc29034a8489acda29bd7f29a5ec1d0714c656fb29c9855edf3
7e0cf7a59292d0373eec29c6a4f399486e909e02baa8ad413722e97b4486523c
2f3274fd4dc5c7f4f973e5a680fb6b394958f49266a3a99cd103e2ffcffdfb2b
13d9a65845eca79610c82eeae121c0d0c3222a4adb53370ec0da591eaf081ce8
05ef6adb0d1d26d2d941e84a0c2babe688bfb9bb0812da123df5964ea1e52436
76b2531a5459118923db18ae4c97ff34cea7eee73f9b00cf27f6ecf7c3f97f46
176456474cd62c2be7167315ac47fea4e05e2fb8a971b4c304c9f601688cc50f
acf9f95a1eac7a8444a974400c33f765129a9b9fe84dd8403e6a293c576860e4
4dbc883effd7a2c9ff7ee165e0ed56444ad57c97baba580f7dd1a743728ac817
c654c841c8e80b6618fd0298a39294507d3b058a22d3bc4bf6d323ce9154a0b7
0e46f7fa5ce71afdf75ed493031d1a030b3b9909c07cea5220445cc4820d4875
d436ff51c5fdd098279d5133c8623b7823b88e1f33f31f53cc3aaa6a6211eddb
25b8744a91072f3ecaa14fffee9c1d7256de81c219785db0b906bc3e29e2ef9f
c1b55d806c9df903356fbe105be7a1d0463b102c4e26a8271369a98a5cb14e51
c149f248d4cdf4d01fc03f543aed40d846ef17e74eff0b075358c1dd30b13cac
29bb68e057d60681bd3466b94644b7688fdb2ed8b35402295e5305d12d1e856e
777dfd2c0b885a4eb84515d04301f4aff70b590b8d520565b57ac2d4f6f033bc
d25c0ab6d874edfefe59e135608f17467e5f9b78c18d8303559e7c8b275892b5
c7878447400f55d61036490b5c1f9984e7dcf63efc3ac9565ffb02c93ed5a639
2a49307d16d3b55c227bd81508ef3355da7ac6f1c975e4469c6603ccd9a485f5
50dfa8ca29459088380f82fc55a59cfa7729aef067138acb1571d43ae0646a23
a5b9afdc1588680771c70ba59cbc736f0d2db940920a4b0347378fe322ad7c51
d08702e6aafae5205af27a737c85827da3c44cd5b453138aa53a8066aad56dbc
a7c24133ef8fd6f0530b32c43d1991d65bb364b7d893fc4a9c5cdcb3161ead1c
f21663ecda1880fcf90f7c06cb74be6a31d1c69b41e772fe8a15aec0d1aefe19
cc4a76c22c4b1f7c0109f2b485cf9556de90909c0a98fc9b5184b45bdcde3c55
c1583a1c0482dadb3f632bf625e0b109ed4ebbdc4253353986f883c1b3018daa
9e22c3d6c49cb367e854e9bcdde45e62a957c50806db28b22a24208c7706acf8
e829158a8c93e3855e144e2172adc3597aa53ca586261772973b416449431b60
2f88817d0a2d6a2001367a5ccb6cf20fccfd8a9c4b341a2acd814b2d19d7dd57
a553e5508bcdae41aa472783c416c4dcfa17b3d0d2cc45ef32d8d0485037c117
af1eed59e457c92db246ccad5ebb8742bc3677e06dc5a2f70fa14529be16f9e7
f1473584bae8060daed28cde641a2cfa0bcc95e3fea848f2ba7f649af87aa556
d2ed84e4723b3bab884bb606362c818c8785ed46b2205d9b4a293247679e0464
f79d51584476fd528b2fc34ab914c268c8874e34f030fc7dc868912c1f50ff90
78706e7e8d5caa745893c2999a1018ab141633393ac8d20f07388d9a2a7686ca
70dd4c25932c1442e55c975cf75029c56e85cd29498e70f14e3a8a481a8c5879
78fbe78d243c0586b1ee0c63104adf0ffe5f28e769e3a2c92caa13bf26951435
9a039f163b1cc501361ffc34f9a2cc53c085655bf5bc96a18187b7d8f4b141b7
5e4fa3fbe4308ed4445d47e654848f15976adbd981ec7106ed62368b68fed017
436495d538b9da1d69257d416760308bd22fbf5a6dbe01a5aa95767bb7e2ed03
06fe2bfd782d70285c1f860c6cfdebc0b20d672b8a6d9274f1411c0cdc5e3e81
8b09d1e3db0fe941a3454b53192f8c887afd8fff041e98e54b63c50a4fde2ca8
34be95657cd37b8b47bbcaf8237f5276f0e0a9004bce1afd79dd7b204b31e81d
45fa9f05d6fd56cb560477af62b41ce6fb0115d9e736adabc2aace1bd63d85bb
ba79651fe79fc065ecdc9117fcc6f7a000751145d83e4d080e253b2c889a3196
1e577d770b7e6857b90cab97a6985fe80e46cce2d1ee39516379c61cbcae4500
05b8157e00f4d966ae8d04e1137a5ca961923a0e613cffd4326575676712b053
529f31d845dc9d92283d461a993d8ea3833be27127295e313ec775360a47c130
ffd1fbf2ffa69cff2b42b0b82b9be6b89e62a5714759c008f0691674e24c7801
52495076aed51fbd8db768cec4d310d4a5bad2cf8b5e9ebd3a6e77e5f29cd570
35bfd03e5ed8895200a5dee47df034fcb8bf8cf299e1f9de618c1767fc6c1d7d
d75e9928a9743783041361ddd40d26f3bdb61d29b15a53ab8891041aa094be38
13ff6e7d4066303bad14622edba3454cec161a9b37862505b707b99b0f3343aa
1a2cf240e437b9d5ef5b490b5b31731349ac04eec558da3cc6fc7f5b9b66dc8c
b9b606dd6114af3a1f3f79bac8e733221fe8752f27d85cd66406f1810dc144d3
b9da3dbb187155fc0dea9a1b6bf304cebaf948128206e2240d79a70fef513718
bc707f6c7f8e2a9e6d681c535d4144e4db13e4f8f935cee3bd07fcc6abfc138b
3739b5
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F6_0 /SOSTRQ+CMR10 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /parenleft/parenright/.notdef/plus/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/equal/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/bracketleft/.notdef/bracketright/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font RAZVEJ+MSBM10
%!PS-AdobeFont-1.0: MSBM10 003.002
%%Title: MSBM10
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name MSBM10.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/MSBM10 known{/MSBM10 findfont dup/UniqueID known{dup
/UniqueID get 5031982 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /RAZVEJ+MSBM10 def
/FontBBox {-55 -420 2343 920 }readonly def
/PaintType 0 def
/FontInfo 7 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name MSBM10.) readonly def
/FullName (MSBM10) readonly def
/FamilyName (Euler) readonly def
/Weight (Medium) readonly def
/ItalicAngle 0 def
/isFixedPitch false def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 69 /E put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce32340dc6f28af40857e4451976e7
5182433cf9f333a38bd841c0d4e68bf9e012eb32a8ffb76b5816306b5edf7c99
8b3a16d9b4bc056662e32c7cd0123dfaeb734c7532e64bbfbf5a60336e646716
efb852c877f440d329172c71f1e5d59ce9473c26b8aef7ad68ef0727b6ec2e0c
02ce8d8b07183838330c0284bd419cbdae42b141d3d4be492473f240ceed931d
46e9f999c5cb3235e2c6daaa2c0169e1991beaea0d704bf49cea3e98e8c2361a
4b60d020d325e4c24518fb902882f4bc8481286273cc533d47ee71b3bfe8c3d9
75d5fad38171e362d9a4fe1882a5f5594a0dad4e1e4e3d163e3371d36b2734d8
07db587f6a93aad7d214ccb4ce5c340ca9dc47609676d78e7f13436f842e6bd7
4331b762999bac9b68a891b346ff06dd2cfbc52b08992e8b350850b12e463c45
cc1a334ad96a8ae1d0c9f8661d949539f09146e8dddc7366dffe811a0336697a
864cef35dba85fd0030ac26b48d980b47989c2f3bda9e1bac7d9c4c9931eb127
46cccba484742992e64f7e48dadff6576003746f19c0f85ca89e6cd45d6fc262
55814d39f4a536ceeca271c8317ea2d8ff8246185296abddf461b18cb9c81aa0
99b6f135fbace9b808b52e7e5a1ff586e5f57ca754ca4380c6dda4f01e35e3b7
427b6eeafa773a2efb583b985259ce0bc1fb80d1411d5a6fa6bd0e2435d30008
3c3c96b2f8488c9c76a07897bb8e3371686fa535bd6896fe5dddb29eb5758229
33ec0e509c033bfab950102249a6bbc46a60c6028ad1dd600d7df2522a468951
497aa874f31b6096ca9aaf63e70c2f86abe6fff812207052c113c285ca3cd285
edbee3b0560ddc8d032fa48a47188df53cdb59ea0f0d64904895f3aee2e61cba
be5220322454ae278f14373b2e930384eb52c7a6e8e1ac6d3002abe1cc7779d5
e2d0ae0bc0239a894801f1d23e32450522f752130bdea2bef11c0ac766cf0950
935a6386901a632ab31d89bcf177013659ae5f502d7ed77ced792c42c1dd6b93
e4b85b0252a51394346bd867303cc804e9bd41817908d4798ab5347d70e50767
65c12ae3661e5c591998ab335d40d0cc6db88dece43bb2737b7ee68288bfb8ff
d9f09a132efb91229ac554cc6b2f7dabd244fae1154afefcd6da55c63257aa47
33b290b6ac144b55ebb8f56188d23e7530c2bb5baf79156b54cf0aae1b38a283
7e1f8d71814be7fee42e6d1eb7644c10a7089ad5dd3ce02ac9cbcd9b1ba94c16
1f85ea7d3e8e40219797f576ceea52e52eca6cfe7da9978523719ca1ad388632
8555e71294f3c05d2adb50b7f07b6153d428b354b347f6e76252955313a67ffd
96de2136ea1c6d51a52659c07e3b5072268c91885a546690efee40b9541acafe
c9f2f6815ef9244e968a39e28903c92eb6f2a4aa4f826850fdb7bf497616807d
54e801fe14ec0e6a76858af1dd0074985e33032ab352682ab14f6e0abbb364c9
c6c52dcad6ec6c1131d7757a618fc27aea0700f5db240b84457429fc80e9a8f9
c91d2b56f85e55cc7df4bd5c0df3ba0e6839060591946161dadcc0d6ef00699e
a28c5f5134b5a2c5b35b7fc309b106210305867e7bf4fef71f6e535788fb6cf6
057dd93625d523a1afb2860f81ba9b8b7fd906307cfeebabd8f455687823d81c
ad7f98bf27b3280a273a83febdea5fd9478735dbdc1fcb3a879ce2d10b0380c3
eda4641731279b9b92355e2b28764c6c8f2c5c2f1e75315b6189588e5bee4dd8
b27bf4a4cf503f8d865d68642b72edb94ed48bc8ff853e591b71985a32c77bb0
e794fd325346e924de113cb55f17cd4b48cb4ce005b5e9b59c4ce048f0774a49
b48e653d67594d88153c66c16c4bfb82d82026094d9009d9f2e7832777546a5d
1d65bef971c2907f9ab72cb0ce90c4b18a3a
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F15_0 /RAZVEJ+MSBM10 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/E/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font XDJWFC+CMSY10
%!PS-AdobeFont-1.0: CMSY10 003.002
%%Title: CMSY10
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMSY10.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMSY10 known{/CMSY10 findfont dup/UniqueID known{dup
/UniqueID get 5096651 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /XDJWFC+CMSY10 def
/FontBBox {-29 -960 1116 775 }readonly def
/PaintType 0 def
/FontInfo 9 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMSY10.) readonly def
/FullName (CMSY10) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle -14.04 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 106 /bar put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5cd06dfe1be899059c588357426d7a0
7b684c079a47d271426064ad18cb9750d8a986d1d67c1b2aeef8ce785cc19c81
de96489f740045c5e342f02da1c9f9f3c167651e646f1a67cf379789e311ef91
511d0f605b045b279357d6fc8537c233e7aee6a4fdbe73e75a39eb206d20a6f6
1021961b748d419ebeeb028b592124e174ca595c108e12725b9875544955cffd
028b698ef742bc8c19f979e35b8e99caddddc89cc6c59733f2a24bc3af36ad86
1319147a4a219ecb92c71915919c4ab77300264235f643a995902219a56d8626
de036037defbd3a2c6bb91c73375b5674e43810b4f7eccb675b36f35d63d9ec2
def21c5fe49b54f92f0d18b89289682cb097244225af6400f6ca98efaf336c9f
c304161e2006b3bedbff4dd36fa7a8f7594c02dab68c077e83335ee6d018f860
8d9a9131325d953d6c38c7e0a34236506c1e70cb6657dafc3c9520131a251350
49034e216ae175cb232c2ef5a3c569ab581f936ef4e8b8c8bccac287f06f24ee
1d15d2819058bd9aebc4ea91b74935f6d411562a453674b14bd76fbf5f298f9e
8fd37f529f9e0450bbbe473b5a4039d8d0228f56330fa15411d7544ce700984e
09593a854180d3100e136beea91daedaac36cca03d82b83d953880307edbd0f0
014451ec8f10b1e30b51c2f9055e906272f02f32085e4b9fbe5a6860a74e274a
74349069b6eb90fce84259d281f037d6de9f42fe557f5f13a87e5c9f668dfb8e
f5e7f4b5ef9f5841b3885a6c8994bfd27fe35fa3cc1dbd5ac68e1c98c0d0ecc3
bd2795e77848b5faf604f01362ca473ac72284a56cabb68f35ba43ddc6158955
5bc6614cbcf4b80872c2cc66b6f4f90c315bf73b34e481705ee8b54eef70fbaa
71424420120f27d8853933e3ad4d8026397b040c88567f440df538120d61d0b5
8232d66e2e006866b60ae46c3f4bda16a2eb5b248bb88a11b3fa4770f0f6c31c
dd13bab11c2f4ac77a63f703a5824638fb765033dce02f584f36c879416fbfb1
ee7eebe75d57711b44824db906885934dfa7f386b811a2598fd5cca2585045f0
4cfd32e35f32b90badb9a96f48957b0a311778d21914c9ea27bfbc75197cbb6f
0df8f6fa574e1f1d529a4594f2a6ed99b98fd302f4fb2694e3986c1f46ff165c
7f4c1102526831ae1e469e62f1a6adcf7d2b876c0d43f85d20a6a5dbc2280884
1c7666d56f832b66cf189c4debed1fb37df76c3f1c632ade8822eead5e7f52ac
e65daa6d86e410d469a7844baa4fc9d28e21490b8cb2d3b2fbe718f55211fe5f
74d3573b99bfccf198c775402823aa742acca713d30b55a09c7b7ce3f5f5517d
6133e546a86c0395bef3387804ac1b07a4d27492485741a8c2ade23bb321da56
ded0fe0d43baca1483566fb397db76ba9eec923fc2b3941f3b949cb13dcbdc3e
2c84c6e3a7abbe5c22abf9b6959a17d152ed0576524395d8a5049c5144680a19
0ed3405f2c9ec716cb9c0fbd6b12168d62666ce74149f8505e02aab39977d99a
13a66449c9487a6b2863f7338378fb901e8ac981ec53ca555049b3667b4bcea9
cd731a850ceecd59afbca1ed2fec76c18fcf5ba1b9fbd81eb84c254fa140eb99
48838693123cde50278e4aa3cbdb7f7691d52cc624b4226855a74d3ff4b3eb3f
e193702ad68437760ed7173ddb5031737de3470f9340a44e92355ef033958954
e5b33866ba86201a7951a68783b94f2984b40dac3037d3e6d2250e850984470c
a4fa92527aa313f3f366e97b87d05e114468dcf43ce4a27b9999e24295cbead6
7dfac0c6d99e7332662743f379dee2b05fc7aed3ae405d631e3893b16e1a3771
278319e6014b88fc346b4f3d17edfeab40d6552092a8dc6c2cdd506f458bde17
e66b02d4992a0e370871035bda2106ecf7fab7ced8e8d35c6fbb825ed724b726
8ce5f3f25d11386c958fe4b773b9268484c12f90e2e25e299a2154e5c480610d
f302e1aceed9d0b3e11681bd5322a13b8fe895fc755e0053890a4135f2993642
3d11dba2766edb9954e308ad998fb1cfbc2285d1f7a9135d2f06cd2d7f7d7b88
d1c6c9409fd3962b8b1c9a690e01fda96361ce706ec9dbe3b4d3e0d57baa0d4e
a98200ef682573f9aae9f09e2000b9d7e14ea41682e4e5ac56dae4cec783bf61
a99a5df4e83fd52c0c02edf26274a16c939868103691ff4f8876c25fa70652e9
ccb3399053205e0350ed215170f709c1901bf7b97236f7bcc13ba5b35a96e8bf
c6e476d81e396b0c79118e16b5489279703b1a44c9d7e320936a19ed319cd03a
f052845dacdd9b627a47433f2225827c65dda57721e8b196cd368dcba55250e8
24e6b7b93affbdd429c9bd8e4523d8e8a56427acc3e5bf1b2db9b60cc832002f
1bc52025f18e7d87d9bf1b8cd8dc170c6dcb85af5afc1ac4a24c0e38cfc0f4d9
8d63cbf3b5cf6f14d902ac8a9b4c48a5d4ba4bdcf4f3b69e2998f507719e2bd7
db63597995c5cdbba59f9b010a135f4dcc8cfd602d40b30730125606fd1b27f4
9ccfb1d0f6a97453a8c9a40f643fddb1581504132883598385c4f76b4e57b559
c0ed46d83ce8427db396e96bb3dbc307df52ed28dad5cf5e32d82510300241fc
fdec6d84bb008cce0fe96c7c6d836fd3c8eca9341951e5ba15ad84a1799d137c
938fda761f12ef2b7e90a49f1ec49445b5638ed4b2d903924dc6ebd72fadf61d
16eb74d88503fc48659a86d95043b4e9764eeee72247367d0ca6ec0dee079f9e
5db531a1411790c08c942b7ce7b028e4b956d5f1df8a47a8ac6c37824b661b57
147ade729f5fed3dfb47227b27aa34cb86584d20a628bf18c395b186ef197a2f
dcb3b6d97ad24cc35a847cb98944011ec6342d0ff9e13045ed70b68a1a5a53fa
b8f341c7e187ac0888b3c8e119d8b841e494b9c1bd746cbeb1ce48fda15b0054
817873ce4da21d8550892ab4a06565a98fa666a6be00776bda87181ef8483129
3708a88f69228dd0c3ef8224301dd8fe81b4abc3563f69bf1212897af3e738c6
c57cbfa53e64ff6a79549a8d81c3b5566dc7e697e11971a7cc6743ca1991f391
efd8c0ba9a01397a05bbe5548843de7f2fc4747eba91c5988605a76f1d2aed97
398cc672cfd5498ba16f6aaf55ed4bf613786aa1ba2e092c06cdf82b6231b0d6
b2f10cc3499b6c444cef515a033381f7b6502d6e6ff4bcf2bd273cd059bddf06
652dec312ff80e8c9f37818c2a453523976487f1a46f8e967b5d43aa3e24fe03
46097a6721d0882aa36fba00d3056a8ad42d4efb81edcda5cdad6ff2388fc54b
775167dd8d709c2a315e130e822ed68a889dcec2ebb10c4c56897ef4c8fffcf8
6d0d146c61ce0d5d2514ec2e22a66090bba95fae51b7691c7f1ae470c0f6c58e
1eca070773920235792e58838f031cd2cdae29f1e61ca254a1ed00a6f664314b
9fa26bababcc8a6add7faba2081b6e307a17aa47ae1de11f7189b78feb61a957
51e9257a84d3184ab2b9d858a41aa2c23374497930c4bea32e04d32389c55b93
23a41d83442345d482927070af462aaba8f5b1de9876ef724fd364ce6e376e0b
a411d2036639832aaf1bec583af5bee73ec7bc9a3a2acdde4c1d6602cd8d15c3
39922661926a3b2b1d7b15bb30870929d0da419267c3b04b2aea81584bc202db
56b6277ad95af3cc411dda29096eeef6cf0bb3d554bc9411c39990db4ccedf0e
4aebeff2e95e4469a8fd5ba6f03a733c9ddcb832c221f114de5587fa7c9b0096
2306f9355684eb66d1558aea7150817df7fcd27c3dff8c9abbbe47c2354f7c50
c306e8739a39f1a71e8e7de4e5932a0a1d2b677041802cb02cc13d7c6aab3235
1143c982379bf5d50c92ef96afb597d81c107f2ee92f46a81b1bc9b9cb30a296
74529ce1ba8a022e221c77650c681a19bf0e5080a065e4d66d70f2ee4a876fb4
40b0b1e29681ff5ff0ea41d27f33a7e25115e9bf421e56f47e24f03945a2ba16
906a3d0a8b5d3f20abe89d7b7705af5f0f3533f7a546ee67d3bfb3349d4299e8
e49bec41a8ab12e1bd71b2cff0cb0f1fdfc0ded134b5078a1e87a490d0ee31ae
506618d409acf32cd653c59f36f4e3bc051ca072a4a75b91ddc17660e00cbcb5
b1fb8d17f4bf7f78f74724ff9f1b84a5eacf2e7da1b9ce0bcc94b7a817dccfbe
46cd999463b0b19a91823d18adc1662117011f2acbbdaa2e062fe77706c48952
38ba2840d9d98b9a7a0d63b8bd40c34e26496d979edda33e5821c86d9565f1ca
40ce6c160e57ff22d2564348e8f89d38d46b17d591053c79f89c4e750d619407
eaa5a8bdc52ea6c6ef02744eb4a5c4886c32b210b86b41495d8729174df80f7f
b653a2e6ff5996d96eb51a828d0606998fd526a82a5e8e1dc79127fc6340000f
e218fc26b7c97c3cdfcec5a497f7be1ed11aedb012ffead9aa2b94630ead80b6
3ca17e79276dec733c9955e9813970215fbe02a751bcdaf5e427a64e9b47b4ef
e105983e0e02c5a8cdc06a5db4126ef333583e4aa17a3fd944ed803d4ef88501
bd626e0d1d8d7b71176259283e22d9382ae88bbec9cd6ba87933f86fe28af800
dc2080f38948e3c20d8f4477e2b9f85da4800cbd1b9015eb64a07b459215caa5
c38b7781d919e199112e241556e1e7681a749cf67a6b246b6b245d34ebaf1504
f06366b8a1faaf10bb4304579640f2cbf3fb339df697701f6c51afa09351e699
890462e1a8152f70f301b5f3a01c549371be46d138045ffed5411192bf6eeb13
51d407ffa26d4b8e7b267a3b3cd5bf9e06816df2e35b6937cccf16b4eb9ca3f1
272a16fd71588054016ef2743c1bd58c6bf22f083fa9326d19299ecbcf66f4b9
afed95e1e2a2f8792328e3af6025da7baa1b10a721bc511e9c2f302673df78b9
f466e742ab2bacd5728bef45dfef5b74d1da674f4b1c8d51a324fa24b23d141a
e082d79c3fea6440336329105d33aa1a960eead51cd500252a4d7d481cc31a99
e9a59e3b4364a3e19805c97270bd19b031146afd9f46111a10bf886385731d74
95ed4727f7e2435c96ba702904ad29f606fe9c5f1f9a11a229b1d528b9fa9ba5
b50b4d4dba0ab5b3840d71c67626b6afcaf743dfe5334e00b64c5a73b3775450
757b911673bcbacfb0f8509e8b2b2d9dada9a1558b97b146f555f85022bb4bce
86862babbcd259be6537133f30ab2895f60869641b1b9a4cb43b676b0739c112
2859492d908c6c60aef5ee3b60d515e7e641d008483ab4aea0e159481d623193
b5e2bb48c77bb87783c7525e59d19a190e2c0aa02446a8d4964844d9f2561a3f
70f20779d197b91450de25463dbb82c2c7c6428706f6d9f6a1474bd85068b37e
4eb45bb80449ca5fea88804308f054167aded26609e7093cd396948cfc810160
347c6d834531d64a27bcfde1dd24607d5209060f8207da7f5ca88011e24e326b
66a261f36f754a37339d7f10eab4f276e1eabff47f4bdb577b9c4dd3de333fd7
8f8da94df25df93a57193b1411761f908510980558e23b0584421f920989a758
138f2e50e1493b3f9f2154a488202e0bb77316ec03f6555de4ae83923dd1588a
fe0bfd9235b4c08a8072804d743e793daf862ae381624303be7e5e0dbd74c51b
4172b1a16c27b6f8c5a695fcf3015cf4f7d89fc91c4c8102eb83a15093263774
740f02f675477a3b4b6734daf3d18d1e3bb7752922e9b33bfadc539596c276bd
cbf0fcf5437eb33fbf4a83bb2f92462236552eb0303ee70602f42bdc4b51d384
301922cad3abd13deb81f173e9deed83786f4a5de1d7aa21cc77fc364fdd2e7d
8b9e8074ebcb7f3511f0a256e2cba9b32bac11a5b7acadc0fc1d378ab3557382
9aaed6a9c679e7e5cac49307549f8c4335fc477267e25506c41035cc248f8797
8c267cb08fb5bf8a087e95dd47aae4d8389e97ea0da1af064d76e5df286a1774
a783e3df200df1cfa26ef1ed9b5dce5dc55102cc5718854fd8911a886d0e2e8c
a38eadf009525bbe17d0986f4e3c6a23e608fe2782e7c4bc31ad13d80ec03b7d
1f0ff0855c4d7f9d63d6283ad8658fb13ff68586e3135a99341e4b88678704a9
c5e8a4c2a9e70f13408c9c54ac9420d52761f62225c64b7c60514b7de0a2c8e3
f27544869c93890e7df32680fdc438392efdd6a7bbe7621a7642632b7f45bf2b
3f0cc935a688266c39f458b9503ed06e67f4094946e73a3fc27494d890065355
4fce63c60e6a32436d5ba5e0ab4f373e816b57fa6ba5a2a9bd02cb58af2783b2
ee1da6169c0f15c23c55a7b2d74edb384c6f646adb73d70e3310873e0c99231b
1af196d1742758956415392b4537b1f04ee4060899648c387bc55df28c6db99d
2f87190bc6f1109ebbd78e15a5641a76198b590286065996f6fe1f776f7013f4
e999219945c4509d37463f6f18cfc46a500f39e2f2ad229bc16793428a9d8cce
c5d950ee8ef43b425e518f4fa99333f9bf2a420b33b383756ebb0324b7df49c6
0eeaff9f5f4f0665fe60d40a1f9824c0df60827d2d3915512fc4a5e54db36580
9e3fd8c1c7c9ead2b0b5011e10ec68e4035d8aa662f0bf09fde9bbeaab5fea32
3cd1f8cd96c62b0410ec741cc2aab05bcf9cb188194aa1fea94f40a4254d9149
82dee90d74a6b5d876068386d55c1ab92f62e3d1c3f24d564615ca3035ffce2b
6b49e53257393e66967da9b72010d0f8c4b6f4337487b6abffbaa16aaa86a6c3
7c22a7b4e6f4ee90d60a9fc7c95b15d34c8a689f028e591215b329d86f35376b
15dffe9323257f0748925c002cac78ce7cf473af7378eda5489e3c464b11e3e4
87d805cded68a70bb95a36d01885006d2cded168532d575a128f0e03ce4a1827
b7b0f7ca3da8e4dc774ee59db3616caa3a8924f84f35df50e48477c35fd08945
308a214bde3389d0cb225ee5d1f96771fe3930b16645c6283b70223dfeca6663
d72e9b6b4773edd543cbeb81e38a094ff9f1eb6012ca08a77092987bb8dfa849
361743964bfd43032f77b09d6d1407abdcca53d424ae51fb1ed1434cf4a2f391
b81678987709e0bea61d8546b8de9b05260d7e2284e445933ecd867cb63b6004
0fc50c76fb25f81fdaaf545bed63d6065def8265028a224797551a6a8ddfab06
84798af0747678d53a7564519116755a795f14b254642293aaa3622be7c14f86
5dd86caf78e0273677f2e33658b24310bf444b1e4f0719c187669b286740775d
66a65699cbc25bea7f7eeb8c3146f9e91e5e0f413376ac09c7e24f9b76d2af1c
b63201760c0a7afae554b8defacb30d9dd146223f69b015b9b7a79cf92d52404
6531acdb6bd53597645241ec6028c585407b903d0579573ebff088e43efa91af
e77940e6c5ffb955e1fa083b949cb13dc3483bc7637b96f03c79426237a96c21
26788fbaf00540a987d4ef95082d64a104dbbd75e4ea5c00c2cd02e622987ff7
2775eeca7c15213edb33fb30b48d17c3bca35ed5ae941829d5992d7bb74f8fb9
b04fd6fa321052a8c2b40f78c8e8eb081f8851c508f4774267d091e2bcfd53fd
bb9e9b22d7aa6c9b62f0f67a3bb9b1984979d55c45d705c1cbea897072a86b4d
0cb7400640c26526c0a03395986cc3ca897453f7e6c4251d81ed29e82f7052c7
f8ded9c0aa221832b5750a9845659235f82bc4d9b073a75af2271a0814b1b9a7
f598e0e7628851b21af4f0b0536c129f6ac5f62090191a7a0776190010de80e2
7e252e134b7a5c4e14a18a84e7fce3f71645ea072ce3655632d2113d4d176f13
29142d814a63c756e0a43ad21a55d932d1b83ec93188d7c893220fbf5157baa0
834ffdf5d191342a4f7afbba2e63b8f36a6394ab5926fcdfdcd8d8cf138fecea
3deb371294591899b4f6f8c8f0ea2c41356eca49df468a952f9c3ffccc8a99e1
0d5d61732eb44e2ae7b254bab320d13990ffcdb63f3d541ed21ae022e86ddf20
1eac6701a072aaf27664dd4e7874c4e428682c44de9d9b14c25fa8c2e8760acd
79f11c13e198602be9d9573f6f04643b80abae1cb6269e00c8ab419d49c3606b
11b1f8f46e7977789b19ee83c5bc35bfc48da6d32dd4d16c1303b0799dfe98fa
0cf8531205195af9e992dac76c6cb79ef51865e6b012f29df6d3333daae56b36
8ede2fc26a580344fdedcdf9c61366f5887fb1e7300f789b9d2e4f5f102a72d9
f9319ddc6ec6194a1c53e78b4b81e1fc473f046326cd7f95e704c32911002f69
03669f5cba83b1c9ad7b77610da3dc15e3685a6dbecb0af4a94714705310fc90
c9ad1333806bf2fd7b6790c706f77cab4db8a00ab088358766b0f063668ee8c3
e4707c093d459fa4fe4f82170c84159ca93a8e94768d507e39f8fab97a2c2f60
35a515a689081ffaf71da924fddede
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F16_0 /XDJWFC+CMSY10 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/bar/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%BeginResource: font NUMAFF+CMMI7
%!PS-AdobeFont-1.0: CMMI7 003.002
%%Title: CMMI7
%Version: 003.002
%%CreationDate: Mon Jul 13 16:17:00 2009
%%Creator: David M. Jones
%Copyright: Copyright (c) 1997, 2009 American Mathematical Society
%Copyright: (<http://www.ams.org>), with Reserved Font Name CMMI7.
% This Font Software is licensed under the SIL Open Font License, Version 1.1.
% This license is in the accompanying file OFL.txt, and is also
% available with a FAQ at: http://scripts.sil.org/OFL.
%%EndComments
FontDirectory/CMMI7 known{/CMMI7 findfont dup/UniqueID known{dup
/UniqueID get 5087382 eq exch/FontType get 1 eq and}{pop false}ifelse
{save true}{false}ifelse}{false}ifelse
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /NUMAFF+CMMI7 def
/FontBBox {-1 -250 1171 750 }readonly def
/PaintType 0 def
/FontInfo 10 dict dup begin
/version (003.002) readonly def
/Notice (Copyright \050c\051 1997, 2009 American Mathematical Society \050<http://www.ams.org>\051, with Reserved Font Name CMMI7.) readonly def
/FullName (CMMI7) readonly def
/FamilyName (Computer Modern) readonly def
/Weight (Medium) readonly def
/ItalicAngle -14.04 def
/isFixedPitch false def
/UnderlinePosition -100 def
/UnderlineThickness 50 def
/ascent 750 def
end readonly def
/Encoding 256 array
0 1 255 {1 index exch /.notdef put} for
dup 107 /k put
dup 116 /t put
readonly def
currentdict end
currentfile eexec
d9d66f633b846ab284bcf8b0411b772de5ce3c05ef98f858322dcea45e0874c5
45d25fe192539d9cda4baa46d9c431465e6abf4e4271f89eded7f37be4b31fb4
7934f62d1f46e8671f6290d6fff601d4937bf71c22d60fb800a15796421e3aa7
72c500501d8b10c0093f6467c553250f7c27b2c3d893772614a846374a85bc4e
bec0b0a89c4c161c3956ece25274b962c854e535f418279fe26d8f83e38c5c89
974e9a224b3cbef90a9277af10e0c7cac8dc11c41dc18b814a7682e5f0248674
11453bc81c443407af56dca20efc9fa776eb9a127b6247134248295bd22993a8
90e59bc557eb047f87afca6de68de675a33bc2806aebaafc9c41dd84b41d360f
709c6051ccc6e5eeb3b1f381dc4af41fffca18038106bc8fae33f0409e1eeca4
f248bc301caf6cc4ab0e2055e21c3d53fa6e313af49a09d71f7a55328e21acd7
caaf0ae5ccb91dc701a5ec1136dcef26ed582164945baa7e8bc36793ddb0d2f9
a58a9767eb5afe5464173fb47d2a188942fc6bd3a8c8253e80d143cb6385cc2d
8841a24d4dd8baa438065f8d14b92f393950059d52b71f0b6cf166a3b12df464
5d820e09acfddfad4555c51bfdc45fd1177e66dd1f9deb2afa6af714adf9910d
a0897e60ba286b917340e828089a905948b6e8a9b588be7be9a93ec073d4d8a8
a49f39b3def7cf9751279425c2a45e8c0bcfa9b58927ad12e503719e541509d4
4cf542912585b0078869f1576c15efbd3b2cc6a44c3cc4505f2016d43d0f8a1e
af86cdf99e303969877cc5a9e8c158371f5052a43a27d3c413ec153cdfc28992
3d96bf0e4662f10ee1ac349f089b4ec77b49fb006320565b16caee525c0c3417
598cae49dc8b2bb1147c0ddf202831428b5152266facb8847f64acaa5c9983b5
df7b44b8737a2001a3a20dde63a2090cf54e66bd4ea2f2bc28a482a3cb3908e6
03fc2962577a2273fc5af339afc8379026f75107b6151a2602fee6cf761cf8fc
2f5f9332027bfb1c33da80a9edcbddb78986112e27c360926f3887cd0d83edbf
ff5c293cf1e1128a7caa33f244043a34e256fbb0c37724db719d509f7363b7c2
e9e99d87a79f2545a8ab671c4f7cee7a3272dd1d51d6e4d342c363fa6798d23d
9e92ff1940e35c128e675e20ffce1c4534f300473918e6329ada01df2141d3da
f6b4654996003755017735681ccb2b55604edf1afba9f1903c1e717bd8e4c6f9
80f2a78e81ed2f96881c121504908414954bfbfdeb38c479caead822dac655a1
fe092b9bc795da3aadbd847fa25b143f00fc119c7cc96d3b3cdf4d2fdad66761
91ecef0d6f689c0a993a5776ccb4c9dc22ffacb20f296a98a1d251bce98dfca9
d477b59aa12165b9898b3bb307d84650143648b24d078d6d475a58ff39517602
6471fee737435ba934c89c9e575d22a26293318a9c634efc8a49fd2f252dee9e
1cdf00fb3e0eb3b99b26cbf6b6bcba9c5bcd93fb034ca7f803b459cdc9c021bf
0f4c2ebe0e45e1655fa2439ec87263f34922da2335706c86240ebce4c1872357
fcc31687ebfdf4d7c5aea2562a131a9c5e2d5a48685d90f9fd884dc364cf26b0
77666f83e4b55ab35f7899b64fa2b5d3f8476f5693e12569d7387a609e143cc7
86bc861353e017c7f07b286acf2e4b52598cf5bffc15237586ee95b9c2e394a6
976e52ced5d69488c44c65b678ebbfd5e79ffe0884a110571f1bbd324ec20bdc
b86d16ff207be283593272eacc704653c0af66a70c02f7a2d4280ea7afa83562
34853b32ba7d24f11c1718c2110a0343157116155ed36000d50556b4785f2ddc
8204df97705cc5daa5ff8d8efa85d0f06636c8d56bb8040fd345b18d57e1daeb
02a7ba31ce78ecf46ef96e99f10358c7a36a89113fb06342dbace1a098f5baef
0318f0344e778e18bce13774342d78944f4b7c2e1ac24a489725cd99362e6af7
85486904aafdf0a13e6c67ee26fed977b0a6ef8885d47c863543571b29a28c97
82a581faf288cdd73699767df414a6343242883e0e02c5a8d2ccf371ac25f17e
e33cadad78cd3460ca416fc3cea16cafbf9552d84e06d79d1719e8b5c348fd2b
16c1252da6938697bbf6569dd2720e8ba9a1572a64046ea9749cd5ade1e61a18
446a8531e01d039bbdeb72fe18dba83d6e0db1ad996ed02e11a94dbabc010895
af248e4a5399a9904e68a2e1fcaf0dc664d9c79a0297f6c858432c892f24138f
1f1ff06b18bd0ccf394635cec4251b41e5c0e082de87bf7f37a7bac9e0d4b7b1
700ee540a1e1ab8774ff0b2bd48ea78e89ab7ebff30ee35e340dbb2c1798ce22
8423986e21b5bdf5a5cb547149be43242ab1380e37fd72f81fcbb91ab7163618
8556a440b87d4dfc6d303ceb1dea4f204b65e527a769ad7d8bef1a4a1d33504f
964f9e42336f159dc6ea576271ff2b350e78dd02795516d9733e4114df4f2e02
62b6b8894221644d15c3bd4b4bd703a121b452d6f95ca2102df639eb169b3b1d
85a901c7510a0f77b982884c256aaf3ce16603d26d741a2c98d73b1cf0428250
3dcaa647ccd4344130de118933495a99551303d5f83fec47dc64177603da28c0
1c62d4728780b2fab45e8d138a39f8b865824dec298823fee08fad12c2e4d4f2
ea2bab6d73e63aaae68402309a55551703bdc7851c2eb9928a7cdb415eba6e16
8501356eb391cbc473844861df59c6900a7830e93c04cf4ba4d285c5ec264b00
6e13cb5fb7cafdb0a9da8ee4bc17821dc2b73dedc46d1f4ed953ad073ab85705
3cc3d43a8a0f3a6ffa923106388ad64d98a0fb692742f533bd3674bba18bd360
e0b7fc6b2a3f5e53623db8029216a2e2a5e8111ba5bbfe6b2c2938a2121fd3c7
cad20ce7b4775f43b705194e8f3ad2e6597e89256420002742f60ff61086dae5
9c1331b38336eff3aef839cc52b0d33f9cecd57671750b147c41b7d7b97abac7
4ee644b01435151b5e14a8fbf6cd49b9820247a09ae7da65c91808c3b4e08360
96afd798cf189dc669ff8a823aa51df4bddb7a36038a35bf94e68ca908cdaad0
b73cf3026b0d9fd7520fc8f03aedbb93e8614a6a3db785ce9dd843116dd11b64
9bcc485008d4b66d6383a656f7fd51e3f1823b6901aa69682cc47210749cbcdb
df3c543829e9cd96ab01aff6733ea0ce93c1f6a87e631c8be4eb305aecd823bb
62998bfa70b172196733846a1e4e971e2781143cbf3b96549ddae2c4931b839e
2dd158a674fd7fd646218c85be00da0a3f09cba25b321fc67d2b2d500b1ffbf5
e9ec4cdb3946e61ec603e26656dd8ef7a4be34c6c9f23420587fbf90b029b3d0
f12b07672d04cbd918cbd9b12a896de17d2892550e9006becf59c491555ed2c9
3e0a2bc0a54a1e46649318cf25beb38aab1dcce73a3dc8e867454d8be400b175
ff5192705681167026375b3971db11516f49eefdfcb55696048f4d325d61c48f
f920c128001fadfce180fd7cb166d92fe2468f72aaf908940f525676fc915ef4
f304f0ae0901f6cc7cc4a92d9470d87847edfdef03ab0f8d9d077f3f2707e78b
67bf7ad8166cb2a89387f8f0ea2ca0e51bceb323b8a69ab941b64346ad999659
6d9e855e0bec408c2e13a6d873d6ba90ef3e1b66215d1cd8d74a11a0d2d34310
47fdb07518bae9d551168ed279438fbcae5773d916e30dc3b0e22689b2814954
1b1146cd804aedbe65cbf30fe88d262db2652456a0cf6b2517b209c4dc16ed96
766c23f62736f19b0b8bb338f8938b0d48dfbe4182d8379ba35db069d7881133
655908da78cbcce4e5882f7919665df00aea3ef801715ee56092f281fab2c200
11e67e27b39d7d0360f333fe04c1e9f2d428e6e431abd6db1f7ec2e97ad4526a
4177f875ae613823744ecab071a1ef05d10ea782a4241001de95831491534f9c
d04f15a2ea4091adbf8bb5bb1be479111d7b31ed46c5abcc0796c383298a5e46
4b81807d4a2ef8d0401dca347a0fdfda31be94e3443324026b192c8130f0a615
c19bb54961d63804a1ab198af9af1c1c91867050dd5172b543c269ac99c8d86b
5d71427e1f26a5831488aefd9e945cb75054575c7d27ba350ec6ea1020c7da43
9f7a9d8f653cef28b9dd15c0051c736ba2a4e86ff107b4392184f8d83f147884
d197e245b594b510ad5bbf01c3e2929ef6b84a3e26e022894282f1091853639a
d78af4191eca7d7f354481e56d445596bc68d4e94b7f314d296bc6f0d8082950
f608252d2f6c117c74eb05b898fe63bdfb177f93e1540c5f68c0df68b101f18d
6bf29787bfbcdc911db687c943b5b16c20f4e0616904266b2730bdef98b597ec
0c8fefb07659886f6b3926cad833f6b314ae3532d858c73872fccd7fe95d36e7
312a4517029603a387586b840c91dbc76406602d7357e3b49160e9045cd28b27
c6fee9cbedbd21e246b4d5d19966b13842b8d666d985c4dca7282900b3af9922
518de02562d14018c5712b925e50b73641d0e4751faac47de00484503a472804
056a83da482a4a7d61226052dad45f9fb5740ec9c5ba4700f41c9ca608eb7b4d
df381f442ab2522cf8e4252dabfeae1152d6ded67f5fcfa2507ac551cc6be5df
047106d44d2956743820be5ee716eaf70db25c6c4b8f9f8d02ad827437235de4
eba2aa12784e95415644506a748751b541b08f1154d938d461f0889ace080daa
421845d6b985e55f63ae05528e109b32764e12c66c46de9b551f27b8e4797ce6
ca4500a3f613d9331bfc1db159466fa060c25d70730a8a0d899525bcf4c9e57a
db440dbe360187a4d3acc998ece0945a02c05c7bb2baeb442d704fc93c8ed1ba
8585dd7d99d04b1cffc85126550ca4e4c8c816062f0cb9d53b79a495a3fdc4d1
651a7a464c98792594f4e78c4ceff967ae4eda9dbba517fb6e05181504a6bd4b
18f623eabeabf9f4d65fbf3a13880e475eb12905e253111238c8bcca5a23a9b4
416829b1ea3c1aae5cd6178b19e65ca32692da965376baf6fe251b4b9751ea8a
e22720e6a37fb107fd1a34398d24bdd58d15480844c9305979682928cae73bf1
5b3b96a898b9b0d1fcd411e7792c45e0f1f9e0d556fbc5d0c84a7f890ecdf7c5
f307fae44f2ddc2b69266c06741e69748f24d8b2cefe85091b18a116d42c887d
e6f1b23ce0fa5bcfe424791dc79fdaa92b8b292892057871304bf5e481e9c4fd
dcd1d7bd74ad89a0749b9390a6bc22102f74842f4d8193add612cb77bbdaf5f9
0a65c91d372b64041c571f7ea2f5622836cfc7883fd9635fce6aa2fa0a5ddbbd
56d5683d2da28228fc5fc75eaa8c1f3a607bcd3fa6ff42bf55fb07d70726a1ba
0106e5dcf4f6d4fe09d93948c4715532f2f92de900319763a680bc64f044b60b
a41943e5c052f835764be645fa6956de21fab8e7f9b9b4b13b71950f921e0f08
e67490fc4f2537577a93f397ed6a7eb1c2ef55675971bc84e5ede78f8e53c11c
96b4dff057cd143c66d5e7694fbccced3ea5584b8e4cef3222c53e39af24899d
1d3addf0ad3be37f06992060906b0a45350d46b0c1011c18426a6c9b117c4481
d7fa3caa75b4be4bda1bef19ec223dfc0138382b2e3317fdbbba5ed8112eeb34
d0f717609c19e694437a927ed189e2061a8ad4f8acdb33c2037b24c91355ba7e
fba89969e5d52e3423cd86efc7ceb6263d1a6d9009cf54b2f7db2c05e7f08cd1
3dcdc2a8ab9a12439d165ea2e26a0dfbe6e046e267b2f1b87b59caf96cb565d6
762f77df70c5867bf5f0ceeb60cfbb7dbb9b983433b51f46c1b2c33328d4042c
63f3931b4922ceab3f9fa33d61f040dc86b464c6ca451c7d9b8d5089512a522a
24d7d463acfcc1dad90d11c24987d80c2d90c49b80edf350d1cc22057422c13c
d79f954ab97995e7c62e5e4d980af960dbaff4d4408fde2b6962a4b31a71bb8b
666b79744caeec627358b10fa130855fa44815f1c82b8e1e90180c99a8b70fc7
25154c8bde7cfa1e716c77a59f86ff3b16f2752d2c25cdd09f05166c1b22516f
29812cb4f6c021acaca5eea3009cdb09110cfd489a8ecbb9f3513aa3c99e1d14
0ce830d6eeb744de31e2e24b3ac5072b3dfc28f4d888ea8458f7100dabb4b133
e3d82d5c6935226ca6b0c461d7a58c69277a4dc29b3fed08f96bc55c30734d12
7c1d6e778bd9cbd4453f3ff8b5387b8f9b2add85c38a580db29da6149794e61a
31822cdf4ac2f2a9884ffa52b4acf38db7a5bcac30a611d03af21c0e18f23a0e
bea02060a4e9066a015633e3a1b6596df1237523b98a4c60dcb74f01a741aa3e
f4653a0a1dcd416bff4eca3417edb6a94ecd16f018ba6b634f71f88c228a8238
1ba7262949daea924092aca08ca50a6d283da85b343471b77f715a1e75cae530
505f2f91d9a7eb3fda227593b9ed85b6bda43b408cb420afced5d8e69f8a9689
226236284e8eff7d64562669f61be11a252a2535ab14a32c2ee5e77f8ba8cb56
926f66f685632e3ba4c1d0eeb88a0b1c61f92f8baf7025c8e77f6ca8a0ffdb09
2a7522184dcc68f936982ce4fca61b891436c5dea5513e6a66f45211a7f51a54
c1ee4ce7edc5a7da0eb413d47b08730e1fc502a76a8f0028c1e6a9ab9317b632
25e9ef30c5822e1991606fb37b4e820429f61965f0756713b6e8168f934227e2
17fa622184293c9684872140c82a3920faa4d92c970a0f2d35fa3c07af7b847a
72c095e75f18842826c868018077cd31053ce16741dceec7adc9db38bb5f5637
93ac16ca652aea23f4f1f750f070ad622d48935f8c8178f2cbb4befe14388288
f02c239b5cf247aeccd831350a87e5dc3d232d0ee7ae82c32932d947c405e9b8
0d5c6e314483a3f7cd3c5fdb7a1a8863b773e28f87959afe29229dd1a6b13b3b
15e5f613937c33feaa50842e6a80b4e6f7317beefc499e2011f68e70231c930f
633e6950db4f04594c96115e70b265aea4ac06e74278d2b440792c34ce00232a
2abc50593209aae29d99aec880cef679e267d8543eabf4f824f85bad96125893
7b4431e97415f03f4bae76fd20b1cb7bfea2d7bad26ade9c99fee9158722c934
257b43eb7b02f367c5aa5018b969d63b1254a14d225f3c022e484e554698d893
87f1cf88c4c48895dc304e994c2b2f6cb912e351cbecad71be5814d70ab2ef9b
77f4d1cd5e57eb77c4fcf0aa51445d189bc37e40387e289422fe5ad2fd559d15
35c19a4b2201d2354454fef30a699798751a7221866c462c6af03caf7f581851
667843e3bc95583a0bf39c25d36c8095c9bb71cbb8d9fed1ec6ea110930a1bea
beb8bf61f23c64bfc45ecfec712407190fbab868195bc58e989837957c08fa00
16b88e2559a2e8d980e1a5eb790cf34ffcc780561302cef28262d2ab31edd903
5d397da3fb8705f17f0b8632f616d4ab90544113ada3a5bccecaf90c1e9f046e
7a3f4c9607513e860c5a8388c0534de9e2bf61eef8f938c51cc5226b9967434c
d48f0ad3d8fb22a8cf93a08f1ecf6c14239ceaa20739169342804d6abd5881c0
7fea33d2addab0c8f6eb6e4519ba7f6054eb73a85bb5b613cdda9fd01c08b24e
afdfd597656ae22e44e8cb1275a70d0b324f5184ce61199ff46a6353986423a8
b4f96f5b5ded22c1f0eb7d92b581c391053aeb85ef2aed1614b579300debbf7d
ee98ebed06fea9445d2c324f51bce3e0975e453aed4d6d5853371cc700005526
ae1c13e580a79b03ec36b568e4f8c266839089f9bd1a406dc5b375655bb0c30e
89317f2e58af67e58840f0a0e7e8a86b5148d24e1356bcec51fabf8c6154ca62
3801e54db8ad4a7d701d707fc710bbeb2b2b1ca51769e953e4bf536afa4039d6
995cdd6714f337db974a88faef3ed6179a3e1b02865a0dfbcb61449098efd8b1
b5d48e407ad8049b71d432d0d8f9b18c96bfd497397b56f76bc132602df6cab3
70c77457c8de596178f69d96706cb5dfcf2450270bb75f9d66221d0aced2f5f0
43b906d1ad16258593b23dfcb4fecf198aa5c28d09c284e096da4aff7153a7b5
d44489ca71b28d8d4ec078b97c338d4eb1970d1a0c716b559a93f8a917dda7f6
de559e13d64772a5bf9d048b00b3cabed2babcd2cc5ee38dee98b10eb1504d69
0003132a179675ca52846bdd495d2231e021aed9f32f2a5ab76537553945afbf
576377a480d93413e1449cb7ebe273d1dec1f68249ce50ff9def3b4a9180ae88
800505af000ffe34ab15083c9513250218e836c454551bad4e272cfa608ea0e9
439b027d24ebb6d33c520c5b6b4a2daa062a95ce9990756911072f7a212fe739
31e35931ea899678040d86a819ea84b9675005084e068623378c111df2dae306
369631afcc9e1030ab1b8a6bbaede3794fd1e1e6feb5753cac6bdb9abbfd3a05
75b406ae1f1e2412c3182f2d1a5db0f1a91f61d44e38f34cd517900fa5f594a9
7a1555d97bf54e8135dff430a933e00747687e36b7b7f0b61c238eb9df7fc488
4a472a03579e5fe2c00c528f2d9012dcbe7ec9ac3175a2de1eca9852644a2776
97f4a7c3520f14ff2ca0b81acbda63beb5de928a515d5a421d065bbc57de78ed
93e3373ab0c627c6a2de800cb6b45b92df20e65788a08b9745f8ad7324c3d20c
79013fa3d674a69c0f728ec98df2ce6cf3ca942aaff8fcfea6720ac2a057c0cc
90e46cba8d81195f9685af4a50a97381ecd49097de783ce665628dc4e287dbc1
018f243a52b3bba41c5fdeb168bbf207162a05387b3d4a8982ec75442fad86fe
1434f0275b8db6d3d348ab8ecdcb84be0791d081f265a9efda468970aa32854a
b5040af8fe7f1e3bee00260b5f10f1e04cc02da1f48073700756b46ce2143191
2b53fb0d085964527bb90cc9748001d04baaad1c119af1a8fe61e20ac9ca1912
03417ea43339e613d9
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
cleartomark
%%EndResource
/F5_0 /NUMAFF+CMMI7 1 1
[ /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/k/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/t/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
  /.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef]
pdfMakeFont
%%EndSetup
pdfStartPage
%%EndPageSetup
[] 0 d
1 i
0 j
0 J
10 M
1 w
/DeviceGray {} cs
[0] sc
/DeviceGray {} CS
[0] SC
false op
false OP
{} settransfer
0 0 344.711 15.446 re
W
q
[1 0 0 1 0 0] Tm
0 0 Td
130.318 2.991 Td
/F4_0 9.9626 Tf
(V)
[5.811185
0] Tj
138.344 2.991 Td
/F6_0 9.9626 Tf
(\()
[3.874455
0] Tj
142.218 2.991 Td
/F4_0 9.9626 Tf
(s)
[4.670467
0] Tj
146.888 2.991 Td
/F6_0 9.9626 Tf
(\))
[3.874455
0] Tj
-278 TJm
(=)
[7.74891
0] Tj
164.046 2.991 Td
/F15_0 9.9626 Tf
(E)
[6.642065
0] Tj
170.688 2.991 Td
/F6_0 9.9626 Tf
([)
[2.76761
0] Tj
173.455 2.991 Td
/F4_0 9.9626 Tf
(G)
[7.833592
0] Tj
181.288 2.991 Td
/F16_0 9.9626 Tf
(j)
[2.76761
0] Tj
184.055 2.991 Td
/F4_0 9.9626 Tf
(S)
[6.109066
0] Tj
190.164 1.496 Td
/F5_0 6.9738 Tf
(t)
[3.009892
0] Tj
196.44 2.991 Td
/F6_0 9.9626 Tf
(=)
[7.74891
0] Tj
206.956 2.991 Td
/F4_0 9.9626 Tf
(s)
[4.670467
0] Tj
211.626 2.991 Td
/F6_0 9.9626 Tf
(])
[2.76761
0] Tj
Q
showpage
%%PageTrailer
pdfEndPage
%%Trailer
end
%%DocumentSuppliedResources:
%%+ font YQYTWD+CMMI10
%%+ font SOSTRQ+CMR10
%%+ font RAZVEJ+MSBM10
%%+ font XDJWFC+CMSY10
%%+ font NUMAFF+CMMI7
%%EOF
