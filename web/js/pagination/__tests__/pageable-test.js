/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */

import _ from "underscore";
import Adapter from "enzyme-adapter-react-16";
import React from "react";
import sinon from "sinon";
import {configure, mount} from "enzyme";

import PaginatedTable from "../paginated-table";
import PagingBlock from "../paging-block";
import PagingTable from "../paging-table";
import Spinner from "../../component/spinner";
import arrayPager from "../../net/list";
import makePageable from "../make-pageable";
import schemas from "../../react/schemas";

configure({adapter: new Adapter()});

const makeRow = (value) => (
  <tr className="row" key={value}>
    <td>{value}</td>
  </tr>
);

const pageFetcher = function (...args) {
  const call = this.props.pager || arrayPager(this.props.list);
  call(...args);
};
const CustomPageable = makePageable(
  pageFetcher,
  class extends React.Component {
    render() {
      return (
        <>
          <PagingTable className="table" {...this.props}>
            {_.map(this.props.data, makeRow)}
          </PagingTable>
          <PagingBlock {...this.props} />
        </>
      );
    }
  },
);

class PageableTable extends React.Component {
  render() {
    return (
      <PaginatedTable
        allData={this.props.list}
        {...this.props}
        makeRow={makeRow}
      />
    );
  }
}

// Since Pageable does work in componentDidMount, we need to update again right after mounting
const mountAndUpdate = (...args) => {
  const wrapper = mount(...args, {
    context: {
      services: {},
    },
    childContextTypes: {
      services: schemas.Services,
    },
  });
  wrapper.update();
  return wrapper;
};

_.each([PageableTable, CustomPageable], (PageableImpl) => {
  describe(`${PageableImpl.constructor.name} pagination`, () => {
    it("can be empty", () => {
      const wrapper = mountAndUpdate(<PageableImpl list={[]} pageSize={10} />);
      expect(wrapper.find(".table").find(Spinner)).toHaveLength(0);
      expect(wrapper.find(".row")).toHaveLength(0);
      expect(wrapper.find(".empty-state")).toHaveLength(0);
      expect(wrapper.find(".paging-block")).toHaveLength(0);
    });

    it("can have an empty state", () => {
      const wrapper = mountAndUpdate(
        <PageableImpl
          emptyState={<div className="empty-state" />}
          list={[]}
          pageSize={10}
        />,
      );
      expect(wrapper.find(".table").find(Spinner)).toHaveLength(0);
      expect(wrapper.find(".row")).toHaveLength(0);
      expect(wrapper.find(".empty-state")).toHaveLength(1);
      expect(wrapper.find(".paging-block")).toHaveLength(0);
    });

    it("can have content", () => {
      const wrapper = mountAndUpdate(
        <PageableImpl list={["a", "b", "c"]} pageSize={10} />,
      );
      expect(wrapper.find(".table").find(Spinner)).toHaveLength(0);
      expect(wrapper.find(".row")).toHaveLength(3);
      expect(wrapper.find(".paging-block")).toHaveLength(0);
    });

    it("can page", () => {
      const wrapper = mountAndUpdate(
        <PageableImpl list={["a", "b", "c"]} pageSize={2} />,
      );
      expect(wrapper.find(".paging-block")).toHaveLength(1);
      expect(wrapper.find(".row")).toHaveLength(2);
      expect(wrapper.find(".pagination > li.active")).toHaveLength(1);
      expect(wrapper.find(".pagination > li.active").text()).toBe("1");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        true,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);

      wrapper.find(".next").simulate("click");
      expect(wrapper.find(".row")).toHaveLength(1);
      expect(wrapper.find(".pagination > li.active").text()).toBe("2");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        false,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(true);

      wrapper.find(".previous").simulate("click");
      expect(wrapper.find(".row")).toHaveLength(2);
      expect(wrapper.find(".pagination > li.active").text()).toBe("1");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        true,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);
    });

    it("can page multiple times", () => {
      const wrapper = mountAndUpdate(
        <PageableImpl list={["a", "b", "c"]} pageSize={1} />,
      );
      expect(wrapper.find(".paging-block")).toHaveLength(1);
      expect(wrapper.find(".row")).toHaveLength(1);
      expect(wrapper.find(".row").text()).toBe("a");
      expect(wrapper.find(".pagination > li.active").text()).toBe("1");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        true,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);

      wrapper.find(".next").simulate("click");
      expect(wrapper.find(".row")).toHaveLength(1);
      expect(wrapper.find(".row").text()).toBe("b");
      expect(wrapper.find(".pagination > li.active").text()).toBe("2");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        false,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);

      wrapper.find(".next").simulate("click");
      expect(wrapper.find(".row")).toHaveLength(1);
      expect(wrapper.find(".row").text()).toBe("c");
      expect(wrapper.find(".pagination > li.active").text()).toBe("3");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        false,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(true);
    });

    it("can render less than 7 pages (5 pages)", () => {
      const items = _.range(50);
      const wrapper = mountAndUpdate(
        <PageableImpl list={items} pageSize={10} />,
      );
      _.each(_.range(1, 6), (index) => {
        expect(wrapper.find(".pagination > li").at(index).text()).toBe(
          index.toString(),
        );
      });
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        true,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);
    });

    it("can page through and render page numbers correctly", () => {
      const items = _.range(95);
      const wrapper = mountAndUpdate(
        <PageableImpl list={items} pageSize={10} />,
      );
      _.each(_.range(1, 5), (index) => {
        expect(wrapper.find(".pagination > li").at(index).text()).toBe(
          index.toString(),
        );
      });
      expect(wrapper.find(".pagination > li").at(6).text()).toBe("...");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        true,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);

      // Click next to page 5
      let numPagesAhead = 4;
      _.each(_.range(1, 1 + numPagesAhead), (index) => {
        wrapper.find(".next").simulate("click");
        expect(wrapper.find(".pagination > li.active").text()).toBe(
          (index + 1).toString(),
        );
      });
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        false,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);

      expect(wrapper.find(".pagination > li").at(2).text()).toBe("...");
      expect(wrapper.find(".pagination > li").at(3).text()).toBe("4");
      expect(wrapper.find(".pagination > li").at(4).text()).toBe("5");
      expect(wrapper.find(".pagination > li").at(5).text()).toBe("6");
      expect(wrapper.find(".pagination > li").at(6).text()).toBe("...");

      // Click next to page 10
      numPagesAhead = 5;
      _.each(_.range(5, 5 + numPagesAhead), (index) => {
        wrapper.find(".next").simulate("click");
        expect(wrapper.find(".pagination > li.active").text()).toBe(
          (index + 1).toString(),
        );
      });

      expect(wrapper.find(".pagination > li").at(2).text()).toBe("...");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        false,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(true);

      expect(wrapper.find(".row")).toHaveLength(5);
    });

    it("can navigate to page numbers directly", () => {
      const items = _.range(95);
      const wrapper = mountAndUpdate(
        <PageableImpl list={items} pageSize={10} />,
      );

      _.each(_.range(1, 5), (index) => {
        expect(wrapper.find(".pagination > li").at(index).text()).toBe(
          index.toString(),
        );
      });
      expect(wrapper.find(".pagination > li").at(6).text()).toBe("...");
      expect(wrapper.find(".previous").parent().hasClass("disabled")).toBe(
        true,
      );
      expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(false);

      wrapper.find(".pagination > li").at(3).find("a").simulate("click");
      expect(wrapper.find(".pagination > li.active").text()).toBe("3");
      expect(wrapper.find(".row").at(0).text()).toBe("20");

      wrapper.find(".pagination > li").at(5).find("a").simulate("click");
      expect(wrapper.find(".pagination > li.active").text()).toBe("5");
      expect(wrapper.find(".row").at(0).text()).toBe("40");
    });

    it("updates url params correctly when next page clicked", () => {
      const items = _.range(100);
      const pageUpdatedMock = sinon.spy();

      const wrapper = mountAndUpdate(
        <PageableImpl
          list={items}
          pageUpdated={pageUpdatedMock}
          pageSize={10}
        />,
      );

      expect(pageUpdatedMock.callCount).toEqual(0);
      wrapper.find(".next").simulate("click");
      expect(pageUpdatedMock.callCount).toEqual(1);
      expect(pageUpdatedMock.getCall(0).args).toEqual([
        {
          page: 1,
        },
        true,
      ]);
    });

    it("updates url params correctly when specific page clicked", () => {
      const items = _.range(100);
      const pageUpdatedMock = sinon.spy();

      const wrapper = mountAndUpdate(
        <PageableImpl
          list={items}
          pageUpdated={pageUpdatedMock}
          pageSize={10}
        />,
      );

      // Click Page 3
      expect(pageUpdatedMock.callCount).toEqual(0);
      wrapper.find(".pagination > li").at(3).find("a").simulate("click");
      expect(pageUpdatedMock.callCount).toEqual(1);
      expect(pageUpdatedMock.getCall(0).args).toEqual([
        {
          page: 2,
        },
        true,
      ]);
    });

    it("updates url params correctly when last page clicked", () => {
      const items = _.range(100);
      const pageUpdatedMock = sinon.spy();

      const wrapper = mountAndUpdate(
        <PageableImpl
          list={items}
          pageUpdated={pageUpdatedMock}
          pageSize={10}
        />,
      );

      // Click last page
      expect(pageUpdatedMock.callCount).toEqual(0);
      wrapper.find(".pagination > li").at(7).find("a").simulate("click");
      expect(pageUpdatedMock.callCount).toEqual(1);
      expect(pageUpdatedMock.getCall(0).args).toEqual([
        {
          page: 9,
        },
        true,
      ]);
    });
  });
});

describe("makePageable calls pager appropriately", () => {
  const PageableImpl = CustomPageable;

  it("pages reasonably", () => {
    const items = _.range(100);
    const pager = sinon.spy(arrayPager(items));
    const wrapper = mountAndUpdate(
      <PageableImpl list={items} pageSize={10} pager={pager} />,
    );
    expect(pager.callCount).toBeLessThan(10);
    _.each(_.range(9), () => wrapper.find(".next").simulate("click"));
    expect(wrapper.find(".next").parent().hasClass("disabled")).toBe(true);
    expect(pager.callCount).toBe(10);
  });

  it("shows spinner while loading", () => {
    const pager = jest.fn();
    const wrapper = mountAndUpdate(
      <PageableImpl
        emptyState={<div className="empty-state" />}
        pager={pager}
        list={[]}
        pageSize={10}
      />,
    );
    expect(wrapper.find(".table").find(Spinner)).toHaveLength(1);
    expect(wrapper.find(".row")).toHaveLength(0);
    expect(wrapper.find(".empty-state")).toHaveLength(0);
    expect(wrapper.find(".paging-block")).toHaveLength(0);
    expect(pager.mock.calls).toHaveLength(1);
  });

  it("shows empty state when done loading", () => {
    const pager = jest.fn();
    const wrapper = mountAndUpdate(
      <PageableImpl
        emptyState={<div className="empty-state" />}
        pager={pager}
        list={[]}
        pageSize={10}
      />,
    );

    const triggerSuccess = pager.mock.calls[0][1];
    triggerSuccess({data: [], paging: {before: null, after: null}});
    wrapper.update();
    expect(wrapper.find(".table").find(Spinner)).toHaveLength(0);
    expect(wrapper.find(".row")).toHaveLength(0);
    expect(wrapper.find(".empty-state")).toHaveLength(1);
    expect(wrapper.find(".paging-block")).toHaveLength(0);
  });

  it("shows content when done loading", () => {
    const pager = jest.fn();
    const wrapper = mountAndUpdate(
      <PageableImpl
        emptyState={<div className="empty-state" />}
        pager={pager}
        list={[]}
        pageSize={10}
      />,
    );

    const triggerSuccess = pager.mock.calls[0][1];
    triggerSuccess({
      data: [1, 2, 3],
      count: 3,
      paging: {before: null, after: null},
    });
    wrapper.update();
    expect(wrapper.find(".table").find(Spinner)).toHaveLength(0);
    expect(wrapper.find(".row")).toHaveLength(3);
    expect(wrapper.find(".empty-state")).toHaveLength(0);
    expect(wrapper.find(".paging-block")).toHaveLength(0);
  });

  it("handles success after unmounting", () => {
    const items = _.range(100);
    const pageUpdatedMock = sinon.spy();
    const pager = jest.fn();
    const wrapper = mountAndUpdate(
      <PageableImpl
        list={items}
        pageUpdated={pageUpdatedMock}
        pager={pager}
        pageSize={10}
      />,
    );
    expect(pager.mock.calls).toHaveLength(1);
    wrapper.unmount();
    const triggerSuccess = pager.mock.calls[0][1];
    triggerSuccess({data: [], paging: {before: null, after: null}});
  });

  it("does not continue to page after reloaded", (done) => {
    const items = _.range(10);
    const pager = jest.fn();
    pager.mockResolvedValueOnce({
      count: 100,
      data: [items],
      paging: {before: 1, after: 1},
    });
    pager.mockResolvedValueOnce({
      count: 10,
      data: [items],
      paging: {before: null, after: null},
    });
    pager.mockResolvedValue({
      count: 100,
      data: [items],
      paging: {before: 1, after: 1},
    });

    const asyncPageFetcher = function (pagingArgs, s, e) {
      return pager(pagingArgs).then(s, e).catch(done.fail);
    };

    const wrapper = mountAndUpdate(
      <PageableImpl list={items} pager={asyncPageFetcher} pageSize={10} />,
    );

    expect(pager.mock.calls).toHaveLength(1);
    const pagingTable = wrapper.childAt(0).childAt(0);
    pagingTable.props().reloadPages(0);
    expect(pager.mock.calls).toHaveLength(2);

    process.nextTick(() => {
      expect(pager.mock.calls).toHaveLength(2);
      done();
    });
  });
});
